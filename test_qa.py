import traceback
try:
    print("trying pipeline...")
    from transformers import pipeline
    p = pipeline('question-answering', model='distilbert-base-cased-distilled-squad')
    print("Success")
except Exception as e:
    with open("error.txt", "w") as f:
        f.write(traceback.format_exc())
