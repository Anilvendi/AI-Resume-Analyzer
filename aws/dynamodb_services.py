import uuid
from datetime import datetime

from aws.aws_config import dynamodb


resume_table = dynamodb.Table("ResumeAnalysis")


def save_resume_analysis(
        user_id,
        file_name,
        job_role,
        ats_score,
        analysis_result
):

    analysis_id = str(uuid.uuid4())

    resume_table.put_item(
        Item={
            "user_id": user_id,
            "analysis_id": analysis_id,
            "file_name": file_name,
            "job_role": job_role,
            "ats_score": ats_score,
            "analysis_result": analysis_result,
            "uploaded_date": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        }
    )

    return True


def get_resume_history(user_id):

    response = resume_table.query(
        KeyConditionExpression="user_id = :uid",
        ExpressionAttributeValues={
            ":uid": user_id
        },
        ScanIndexForward=False  # newest analysis first
    )

    return response.get("Items", [])


def delete_resume_analysis(user_id, analysis_id):

    resume_table.delete_item(
        Key={
            "user_id": user_id,
            "analysis_id": analysis_id
        }
    )

    return True
