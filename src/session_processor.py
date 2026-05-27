from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, ArrayType
from typing import Optional
from datetime import datetime, timedelta

from .models import SessionFeatures


class SessionProcessor:
    """
    Processes clickstream session data to extract user behavior features.
    """

    TABLE_NAME = "ml_online_clickstream_prod.public.online_fs"

    def __init__(self, spark: Optional[SparkSession] = None):
        """
        Initialize session processor.

        Args:
            spark: SparkSession (if None, will get or create one)
        """
        self.spark = spark or SparkSession.builder.getOrCreate()

    def get_session_features(
        self,
        user_id: Optional[str] = None,
        minutes_back: int = 30,
        end_time: Optional[datetime] = None,
        session_id: Optional[str] = None
    ) -> SessionFeatures:
        """
        Extract session features for a user timeframe or a specific session.

        Args:
            user_id: User identifier (required if session_id is not provided)
            minutes_back: Number of minutes to look back from end_time
            end_time: End of the time window (defaults to current time)
            session_id: Session identifier (stag_id); takes priority over user_id + minutes_back

        Returns:
            SessionFeatures dataclass with extracted features
        """
        if session_id is None and user_id is None:
            raise ValueError("Either user_id or session_id must be provided")

        session_df = self._get_session_data(user_id, minutes_back, end_time, session_id)

        loved_ids = self._extract_loved_ids(session_df)
        basket_ids = self._extract_basket_ids(session_df)
        viewed_ids = self._extract_viewed_ids(session_df)
        purchased_ids = self._extract_purchased_ids(session_df)
        banner_ids = self._extract_banner_ids(session_df)
        unloved_ids = self._extract_unloved_ids(session_df)
        removed_basket_ids = self._extract_removed_basket_ids(session_df)

        return SessionFeatures(
            loved_ids=loved_ids,
            basket_ids=basket_ids,
            viewed_ids=viewed_ids,
            purchased_ids=purchased_ids,
            banner_ids=banner_ids,
            unloved_ids=unloved_ids,
            removed_basket_ids=removed_basket_ids
        )

    def _get_session_data(
        self,
        user_id: Optional[str],
        minutes_back: int,
        end_time: Optional[datetime] = None,
        session_id: Optional[str] = None
    ) -> DataFrame:
        """
        Retrieve session data filtered by session_id or by user_id + timeframe.
        Parses json_value column to extract path, product_ids, sku_ids, and sid.

        Args:
            user_id: User identifier (used when session_id is None)
            minutes_back: Number of minutes to look back
            end_time: End of the time window
            session_id: Session identifier (stag_id); takes priority when provided

        Returns:
            DataFrame with session events and parsed JSON fields
        """
        df = self.spark.read.table(self.TABLE_NAME)
        json_schema = StructType([
            StructField("path", StringType(), True),
            StructField("product_ids", ArrayType(StringType()), True),
            StructField("sku_ids", ArrayType(StringType()), True),
            StructField("sid", StringType(), True),
            StructField("price", StringType(), True),
            StructField("quantity", StringType(), True)
        ])
        df = df.withColumn("parsed_json", F.from_json(F.col("json_value"), json_schema))
        df = df.withColumn("path", F.col("parsed_json.path"))
        df = df.withColumn("product_ids", F.col("parsed_json.product_ids"))
        df = df.withColumn("sku_ids", F.col("parsed_json.sku_ids"))
        df = df.withColumn("sid", F.col("parsed_json.sid"))

        if session_id is not None:
            return df.filter(F.col("stag_id") == session_id)

        if end_time:
            return df.filter(
                (F.col("atg_id") == user_id) &
                (F.col("event_time") <= end_time) &
                (F.col("event_time") >= end_time - timedelta(minutes=minutes_back))
            )
        return df.filter(
            (F.col("atg_id") == user_id) &
            (F.col("event_time") >= F.current_timestamp() - F.expr(f"INTERVAL {minutes_back} MINUTES"))
        )

    def _extract_loved_ids(self, session_df: DataFrame) -> list[str]:
        """
        Extract product IDs from 'add to loves' events.

        Args:
            session_df: DataFrame with session events

        Returns:
            List of loved product IDs
        """
        loved_df = session_df.filter(F.col("event_type") == "add to loves")

        ids = []
        product_df = loved_df.filter(F.col("product_ids").isNotNull())
        if product_df.count() > 0:
            product_rows = product_df.select(F.explode("product_ids").alias("id")).distinct().collect()
            ids.extend([row.id for row in product_rows if row.id])

        return list(set(ids))

    def _extract_basket_ids(self, session_df: DataFrame) -> list[str]:
        """
        Extract product IDs from 'add to basket' events.

        Args:
            session_df: DataFrame with session events

        Returns:
            List of basket product IDs
        """
        basket_df = session_df.filter(F.col("event_type") == "add to basket")

        ids = []
        product_df = basket_df.filter(F.col("product_ids").isNotNull())
        if product_df.count() > 0:
            product_rows = product_df.select(F.explode("product_ids").alias("id")).distinct().collect()
            ids.extend([row.id for row in product_rows if row.id])

        return list(set(ids))

    def _extract_viewed_ids(self, session_df: DataFrame) -> list[str]:
        """
        Extract product IDs from 'page view' events.

        Args:
            session_df: DataFrame with session events

        Returns:
            List of viewed product IDs
        """

        page_views = session_df.filter(F.col("event_type") == "page view")

        ids = []
        product_df = page_views.filter(F.col("product_ids").isNotNull())
        if product_df.count() > 0:
            product_rows = product_df.select(F.explode("product_ids").alias("id")).distinct().collect()
            ids.extend([row.id for row in product_rows if row.id])

        return list(set(ids))

    def _extract_purchased_ids(self, session_df: DataFrame) -> list[str]:
        """
        Extract product IDs from 'purchase' events.

        Args:
            session_df: DataFrame with session events

        Returns:
            List of purchased product IDs
        """
        purchase_df = session_df.filter(F.col("event_type") == "purchase")

        ids = []
        product_df = purchase_df.filter(F.col("product_ids").isNotNull())
        if product_df.count() > 0:
            product_rows = product_df.select(F.explode("product_ids").alias("id")).distinct().collect()
            ids.extend([row.id for row in product_rows if row.id])

        return list(set(ids))

    def _extract_unloved_ids(self, session_df: DataFrame) -> list[str]:
        """
        Extract product IDs from 'un love' events.

        Args:
            session_df: DataFrame with session events

        Returns:
            List of unloved product IDs
        """
        unloved_df = session_df.filter(F.col("event_type") == "un love")

        ids = []
        product_df = unloved_df.filter(F.col("product_ids").isNotNull())
        if product_df.count() > 0:
            product_rows = product_df.select(F.explode("product_ids").alias("id")).distinct().collect()
            ids.extend([row.id for row in product_rows if row.id])

        return list(set(ids))

    def _extract_removed_basket_ids(self, session_df: DataFrame) -> list[str]:
        """
        Extract product IDs from 'remove from basket' events.

        Args:
            session_df: DataFrame with session events

        Returns:
            List of removed basket product IDs
        """
        removed_df = session_df.filter(F.col("event_type") == "remove from basket")

        ids = []
        product_df = removed_df.filter(F.col("product_ids").isNotNull())
        if product_df.count() > 0:
            product_rows = product_df.select(F.explode("product_ids").alias("id")).distinct().collect()
            ids.extend([row.id for row in product_rows if row.id])

        return list(set(ids))

    def _extract_banner_ids(self, session_df: DataFrame) -> list[str]:
        """
        Extract banner SIDs from 'cms viewable impression' events.

        Args:
            session_df: DataFrame with session events

        Returns:
            List of banner SIDs
        """

        cms_impressions = session_df.filter(F.col("event_type") == "cms viewable impression")

        ids = []
        sid_df = cms_impressions.filter(F.col("sid").isNotNull())
        if sid_df.count() > 0:
            sid_rows = sid_df.select(F.col("sid")).distinct().collect()
            ids.extend([row.sid for row in sid_rows if row.sid])

        return list(set(ids))
