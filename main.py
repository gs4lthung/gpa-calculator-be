import codecs
from io import StringIO, BytesIO

from fastapi import FastAPI, UploadFile, HTTPException
import pandas as pd
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost:4321"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


async def read_file(file: UploadFile):
    if not file.filename.endswith("xls"):
        raise HTTPException(status_code=400, detail="<UNK>")

    # Reading and decode xls file
    data = await file.read()
    data = pd.read_excel(BytesIO(data), engine="xlrd")
    data = data.dropna(axis=0, how='all')  # Drop rows where all elements are NaN
    return data.to_dict(orient="records")


async def cal_gpa(data: list):
    total_points = 0
    total_credits = 0
    for row in data:
        is_do_not_count = True if row['Unnamed: 10'] == "*" else False
        if not is_do_not_count:
            is_passed = True if row['Status'] == 'Passed' else False
            if not is_passed:
                continue
            grade = row['Grade']
            credit = row['Credit']
            total_credits += float(credit)
            total_points += float(grade) * float(credit)

    result = round(total_points / total_credits, 2)
    return {
        "result": result,
        "total_credits": total_credits,
        "total_points": total_points,
    }


@app.post("/gpa")
async def gpa_calculator(file: UploadFile):
    # Reading and decode xls file
    data = await read_file(file)

    # Calculating GPA
    gpa_rs = await cal_gpa(data)

    return {
        "gpa": gpa_rs["result"],
    }


@app.post("/gpa/target")
async def gpa_target_calculator(file: UploadFile, target_gpa):
    data = await read_file(file)

    gpa_rs = await cal_gpa(data)
    total_gpa = gpa_rs["result"]
    target_gpa = float(target_gpa)
    if target_gpa < total_gpa:
        raise HTTPException(status_code=400, detail="Target GPA must be greater than current GPA")

    total_credits = gpa_rs["total_credits"]
    total_points = gpa_rs["total_points"]
    remain_credits = 0
    largest_no = 0

    not_counted_rows_subject_code = [
        "LUK Global 1",
        "LUK Global 2",
        "LUK Global 3",
        "LUK Global 4",
        "English 5 (University success)",
    ]

    for row in data:
        is_no_valid = False if row['No'] == "(*) Môn điều kiện tốt nghiệp, không tính vào điểm trung bình tích lũy" or \
                               row['No'] == "nan" or \
                               row['No'] == "No" else True
        is_do_not_count = True if row['Unnamed: 10'] == "*" else False
        if not is_do_not_count and is_no_valid:
            if float(row['No']) > largest_no:
                largest_no = float(row['No'])

        print(largest_no)

    for row in data:
        is_do_not_count = True if row['Unnamed: 10'] == "*" else False
        is_not_counted_rows_semester_subject_code = True if row[
                                                                'Subject Code'] in not_counted_rows_subject_code else False
        if not is_do_not_count and not is_not_counted_rows_semester_subject_code:
            is_passed = True if row['Status'] == 'Passed' else False
            if not is_passed:
                is_no_valid = False if row[
                                           'No'] == "(*) Môn điều kiện tốt nghiệp, không tính vào điểm trung bình tích lũy" or \
                                       row['No'] == "No" else True
                if is_no_valid:
                    if float(row['No']) == largest_no:
                        print(row)
                        remain_credits += 10
                    else:
                        print(row)
                        remain_credits += 3

    avg_target = (target_gpa * (total_credits + remain_credits) - total_points) / remain_credits

    return {
        "avg_target": round(avg_target, 2),
    }
