from datasets import Dataset

from ragas import evaluate

from ragas.metrics import (
    faithfulness,
    answer_relevancy
)

from ragas.llms import LangchainLLMWrapper

from ragas.embeddings import (
    LangchainEmbeddingsWrapper
)

from app.llm.generator import get_llm

from langchain_huggingface import (
    HuggingFaceEmbeddings
)



def evaluate_rag(
    question,
    answer,
    contexts
):

    # accept plain strings or the {"text": ...} dicts returned by hybrid_retriever
    contexts = [c["text"] if isinstance(c, dict) else c for c in contexts]

    data = {
        "question": [question],

        "answer": [answer],

        "contexts": [contexts]
    }


    dataset = Dataset.from_dict(data)


    evaluator_llm = LangchainLLMWrapper(
        get_llm()
    )


    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


    evaluator_embeddings = (
        LangchainEmbeddingsWrapper(
            embedding_model
        )
    )


    result = evaluate(
        dataset,
        metrics=[
            faithfulness,
            answer_relevancy
        ],
        llm=evaluator_llm,
        embeddings=evaluator_embeddings
    )


    return result