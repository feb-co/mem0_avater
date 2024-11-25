# Mem0 - 智能对话记忆系统

## 简介

Mem0 是一个智能对话记忆系统，它能够从对话中提取和管理两种类型的长时记忆：上下文记忆(Context)和观察记忆(Observation)。系统通过向量存储和图结构来组织记忆，支持高效的检索和更新。

<p style="display: flex;">
  <img src="https://media.tenor.com/K3j9pwWlME0AAAAi/fire-flame.gif" alt="Graph Memory Integration" style="width: 25px; margin-right: 10px;" />
  <span style="font-size: 1.2em;">New Feature: Introducing Graph Memory. Check out our <a href="https://docs.mem0.ai/open-source/graph-memory" target="_blank">documentation</a>.</span>
</p>

## 核心特性

### 1. 双重记忆模型

- **上下文记忆 (Context)**
  - 存储完整的对话会话内容
  - 保持对话的时序和完整性
  - 支持上下文关联分析

- **观察记忆 (Observation)**
  - 从对话中提取关键事实和观察
  - 自动合并和更新相关记忆
  - 支持结构化的知识积累

### 2. 智能记忆管理

- 自动提取观察并与已有记忆比对
- 智能决策记忆的添加/更新/删除
- 支持基于相似度的记忆检索
- 维护记忆间的关系图谱

### 3. 上下文感知

- 自动分析对话片段在整体中的位置
- 生成上下文解释以增强检索效果
- 支持多轮对话的上下文理解

## 技术实现

### 1. 核心组件

```
class ChatMemory(Memory):
    def __init__(self, config: MemoryConfig = MemoryConfig()):
        
        if not hasattr(config, 'version'):
            print("Warning: config missing version field")
            config.version = 'v1.0'
            
        super().__init__(config)
        
        if not hasattr(self, 'api_version'):
            self.api_version = self.config.version
        
        self.memory_base_worker = MemoryBaseWorker(config)
```

系统主要由以下组件构成：
- ChatMemory: 对外提供记忆管理接口
- MemoryBaseWorker: 处理基础记忆操作
- VectorStore: 向量化存储和检索
- LLM: 大语言模型接口

### 2. 记忆处理流程

#### 添加记忆

```
    def _add_to_vector_store(self, messages, metadata, filters, context_explain=True):
        metadata['agent_id'] = 'context'
        self._add_observation_to_vector_store(messages, deepcopy(metadata), filters)

        parsed_messages = self.parse_messages_session(messages)
        print(parsed_messages)
        if context_explain:
            parsed_messages = self.get_context_explanation(parsed_messages, metadata)
        
        returned_memories = []
        
        for msg_session in parsed_messages:
            try:
                memory_id = self._create_memory(
                    data=msg_session, existing_embeddings={}, metadata=metadata
                )
                returned_memories.append(
                    {
                        "id": memory_id,
                        "memory": msg_session,
                        "event": "ADD",
                    }
                )
            except Exception as e:
                logging.error(f"Error in new_memories_with_actions: {e}")

        capture_event("mem0.add", self, {"version": self.api_version, "keys": list(filters.keys())})

        return returned_memories
```

系统会同时:
- 添加上下文记忆
- 提取和添加观察记忆
- 生成上下文解释

#### 观察提取
```
    def get_observation(self, messages, metadata):
        metadata = metadata or {}
        
        parsed_message = self.parse_messages(messages)

        def get_observation_prompts():
            user_name = metadata.get("user_id", "USER").rstrip("_observation")
            
            prompt_list = [
                OBSERVATION_RETRIEVAL_PROMPT.format(user_name=user_name, num_obs=5),
                OBSERVATION_FEWSHOT_PROMPT.format(user_name=user_name),
            ]
            
            return '\n\n'.join(prompt_list), f"Input: {parsed_message}"

        if self.custom_prompt:
            system_prompt = self.custom_prompt
            user_prompt = f"Input: {parsed_message}"
        else:
            system_prompt, user_prompt = get_observation_prompts()

        response = self.llm.generate_response(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            # response_format={"type": "json_object"},
        )
        
        def response_parse(response_text):
            print(response_text)
            results = []
            for line in response_text.split("\n"):
                line = line.strip()
                if not line:
                    continue
                matches = [match.group(1) for match in self.PATTERN_V1.finditer(line)]
                if matches:
                    results.append(matches[2])
            return results
        try:
            new_retrieved_obs = response_parse(response)
        except Exception as e:
            logging.error(f"Error in new_retrieved_obs: {e}")
            new_retrieved_obs = []

        return new_retrieved_obs
```

## 配置和使用
### 基础配置


#### 上下文解释处理
```
config = {
    "llm": {
        "provider": "openai",
        "config": {
            "model": "gpt-4",
            "temperature": 0.2,
            "max_tokens": 1500
        }
    }
}
```

#### 使用示例
```
# 初始化记忆系统
memory = ChatMemory.from_config(config)

# 添加记忆
memory.add(
    "I am working on improving my tennis skills.",
    user_id="alice",
    metadata={"category": "hobbies"}
)

# 检索记忆
memories = memory.search(
    query="What are Alice's hobbies?",
    user_id="alice",
    agent_id="observation"  # 或 "context"
)
```

## API 说明

### 主要方法

- `add()`: 添加新记忆
- `search()`: 检索相关记忆
- `get_all()`: 获取所有记忆
- `get_context_explanation()`: 获取上下文解释

### 必要参数

每个操作都需要提供以下标识符之一：
- user_id: 用户标识
- agent_id: 代理标识
- run_id: 运行标识

## 注意事项

1. 确保正确配置 LLM 和向量存储参数
2. 记忆操作需要提供必要的标识符
3. 选择合适的记忆类型(context/observation)进行检索
4. 注意处理大规模记忆时的性能影响