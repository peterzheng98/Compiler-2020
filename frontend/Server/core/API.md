# Basic API for judge

## GET /fetchServerStatus

- Send Parameter: None
- Return:
  - Code: int (default: 200)
  - Message: Dict
    - error-compile: If this key exists in the dict, the marshal method failed.
    - error-semantic: If this key exists in the dict, the marshal method failed.
    - error-codegen: If this key exists in the dict, the marshal method failed.
    - error-optimize: If this key exists in the dict, the marshal method failed.
    - compile: Dict for all the compile message(dict: [timestamp: int] -> [JudgePoolElement]).
    - semantic: List for all the semantic message(list: [JudgePoolElement]).
    - codegen: List for all the codegen message(list: [JudgePoolElement]).
    - optimize: List for all the optimize message(list: [JudgePoolElement]).

## POST /modifyServer

- Send Parameter: dict{code: int, message: dict([string] -> list[string])}
  - code: Any integer value is acceptable.
  - message: dict([string] -> list[string])
    - passkey: Authorized key on list[0], other position will be omitted.
    - all: Clear all semantic/codegen/optimize/compiling pools if the length of list is not 0.
    - compile: list for the identifier to be removed. Notice that if the identification is not in the pool, nothing will be done.
    - semantic/codegen/optimize: Clear semantic/codegen/optimize pools if the length of list is not 0.
- Return:
  - Code: int (default: 200), 400: Format error, 403: Unauthorized.
  - Message: string
  
