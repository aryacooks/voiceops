from .llm import complete
from .prompts import STEP1
def answer(question):
    return {'reply':complete([{'role':'system','content':STEP1},{'role':'user','content':question}]).content or ''}
