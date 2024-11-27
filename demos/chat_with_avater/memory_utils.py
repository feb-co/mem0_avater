import json

from mem0.configs.base import MemoryConfig
from mem0.configs.history.my_sql import MysqlConfig
from mem0.configs.vector_stores.esvector import ESVectorConfig
from mem0.database.history.configs import HistoryDBConfig
from mem0.vector_stores.configs import VectorStoreConfig


class ProfileSchema:
    @classmethod
    def from_json_str(cls, json_str: str):
        json_data = json.loads(json_str)
        user_profile = cls()

        for key, value in json_data.get("basic", {}).items():
            if key in UserProfilePrompts.BASIC_PROFILE_KEYWORDS or key == "Name":
                user_profile.basic[key] = ProfileDetail(
                    value=value.get("value", None), refused=value.get("refused", False)
                )

        for key, value in json_data.get("work_life", {}).items():
            if key in UserProfilePrompts.WORK_LIFE_PROFILE_KEYWORDS:
                user_profile.work_life[key] = ProfileDetail(
                    value=value.get("value", None), refused=value.get("refused", False)
                )
        for key, value in json_data.get("eip", {}).items():
            if key in UserProfilePrompts.EIP_PROFILE_KEYWORDS:
                user_profile.eip[key] = ProfileDetail(
                    value=value.get("value", None), refused=value.get("refused", False)
                )

        return user_profile


def get_memory_config():
    config = MemoryConfig()
    
    # database
    config.vector_store = VectorStoreConfig(
        provider="esvector",
        config=ESVectorConfig(
            # endpoint="https://ec74fdd3f31c4c50af17af6fb3ecef88.eastus2.azure.elastic-cloud.com:443",
            # api_key="YV9DajFZMEJhXzNna3RsWTVPMHE6QUdEb1gzVFJUai00TkxGRFVTeF9vZw==",    
            endpoint="http://localhost:9200",
        ).model_dump(),
    )
    config.history_db = HistoryDBConfig(
        provider="mysql",
        config=MysqlConfig(
            url="mysql+aiomysql://dfoadmin:F2RKGt75.&@digitalray-mysql-dev.mysql.database.azure.com:3306/digital_ray_dev"
        ).model_dump(),
    )
    config.profile_db = HistoryDBConfig(
        provider="mysql",
        config=MysqlConfig(
            url="mysql+aiomysql://dfoadmin:F2RKGt75.&@digitalray-mysql-dev.mysql.database.azure.com:3306/digital_ray_dev"
        ).model_dump(),
    )

    # schema
    config.profile_schema = ProfileSchema
    
    # llm

    return config
