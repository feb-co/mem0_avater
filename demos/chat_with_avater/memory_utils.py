import json
from dataclasses import dataclass, field
from typing import Optional, Dict, List

from mem0.configs.base import MemoryConfig
from mem0.configs.history.my_sql import MysqlConfig
from mem0.configs.vector_stores.esvector import ESVectorConfig
from mem0.database.configs import DBConfig
from mem0.vector_stores.configs import VectorStoreConfig


@dataclass
class ProfileDetail:
    value: Optional[str] = None
    refused: bool = False


@dataclass
class UserProfileDetails:
    basic: Dict[str, ProfileDetail] = field(default_factory=dict)
    work_life: Dict[str, ProfileDetail] = field(default_factory=dict)
    eip: Dict[str, ProfileDetail] = field(default_factory=dict)
    
    @classmethod
    def from_json_str(cls, json_str: str):
        json_data = json.loads(json_str)
        user_profile = cls()

        for category in cls.get_profile_category():
            for key, value in json_data.get(category, {}).items():
                getattr(user_profile, category)[key] = ProfileDetail(
                    value=value.get("value", None), refused=value.get("refused", False)
                )

        return user_profile

    @classmethod
    def get_profile_category(cls):
        return ["basic", "work_life", "eip"]
        

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
    config.history_db = DBConfig(
        provider="mysql",
        config=MysqlConfig(
            url="mysql+aiomysql://dfoadmin:F2RKGt75.&@digitalray-mysql-dev.mysql.database.azure.com:3306/digital_ray_dev"
        ).model_dump(),
    )
    config.profile_db = config.history_db

    # schema
    config.profile_schema = UserProfileDetails
    
    # llm

    return config
