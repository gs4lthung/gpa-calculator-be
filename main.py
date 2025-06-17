from io import BytesIO, StringIO

from fastapi import FastAPI, UploadFile, HTTPException
import pandas as pd

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.post("/gpa")
async def gpa_calculator(file: UploadFile):
    if not file.filename.endswith("xls"):
        raise HTTPException(status_code=400, detail="<UNK>")

    # Reading and decode xls file
    data = await file.read()
    data = data.decode("utf-16")
    data = pd.read_html(StringIO(data))[0]
    data = data.to_dict(orient="records")

    print(data[10])

    total_points = 0
    total_credits = 0
    for row in data:
        is_do_not_count = True if row[('Unnamed: 10_level_0', 'Unnamed: 10_level_1')] == "*" else False
        if not is_do_not_count:
            is_passed = True if row[('Status', 'Unnamed: 9_level_1')] == 'Passed' else False
            if not is_passed:
                continue
            grade = row[('Grade', 'Unnamed: 8_level_1')]
            credit = row[('Credit', 'Unnamed: 7_level_1')]
            total_credits += float(credit)
            total_points += float(grade) * float(credit)

    result = round(total_points / total_credits, 2)

    return {"gpa": result}
