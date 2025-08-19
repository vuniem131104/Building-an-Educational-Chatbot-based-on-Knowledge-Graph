from collections import defaultdict

import pandas as pd
from neo4j import AsyncResult

async def to_df(result: AsyncResult) -> pd.DataFrame:
    """Convert Cypher query result to pandas.DataFrame

    Args:
        result (AsyncResult): Cypher Result Stream Buffer

    Returns:
        pd.DataFrame: pandas.DataFrame
    """
    keys = result.keys()
    df = defaultdict(list)
    async for record in result:
        for k in keys:
            data = record.data()
            df[k].append(data[k])
    return pd.DataFrame(df)