from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
# from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Candidate, JobPosting, BotJobCandidateQuestion,InterviewSchedule,Resume
from questions.ques_framework import *
import os
import threading
from werkzeug.utils import secure_filename
from django.conf import settings
from .utils import log_function_call
from django.utils.deprecation import MiddlewareMixin
import uuid 
import boto3
from decouple import config
import logging
from io import BytesIO
from PyPDF2.errors import PdfReadError

logger = logging.getLogger(__name__)
sqs = boto3.client(
    'sqs',
    aws_access_key_id=config('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=config('AWS_SECRET_ACCESS_KEY'),
    region_name=config('AWS_REGION', 'us-east-1')  
)
class CorrelationIdMiddleware(MiddlewareMixin):
    def process_request(self, request):
        try:
            request.correlation_id = str(uuid.uuid4())
            logger.info(f"Generated Correlation ID: {request.correlation_id} for request path: {request.path}")
        except Exception as e:
            logger.exception("Error generating Correlation ID.")
            request.correlation_id = None  # Fallback in case of error

    def process_response(self, request, response):
        try:
            response['X-Correlation-ID'] = request.correlation_id
            logger.info(f"Added Correlation ID: {request.correlation_id} to response for request path: {request.path}")
        except Exception as e:
            logger.exception("Error adding Correlation ID to response.")
        return response


# class QuestionsView1(APIView):
#     # authentication_classes = [JWTAuthentication]
#     # permission_classes = [IsAuthenticated]
#     permission_classes = [AllowAny]
#     # def get_permissions(self):
#     #     if self.request.method == 'POST':
#     #         return [AllowAny()]
#     #     return [IsAuthenticated()]
#     def send_message_to_sqs(self, message_body, message_group_id):
#         """
#         Sends a message to the SQS queue.
#         """
#         try:
#             response = sqs.send_message(
#                 QueueUrl=config('send_message_to_sqs'),
#                 MessageBody=message_body,
#                 MessageGroupId=message_group_id,
#                 MessageDeduplicationId=str(uuid.uuid4()) 
#             )
#             logger.info(f"Message sent to SQS: {response['MessageId']}")
#         except Exception as e:
#             logger.exception("Error sending message to SQS.")
#     def receive_message_from_sqs(self):
#         try:
#             response = sqs.receive_message(
#                 QueueUrl=config('receive_message_from_sqs'),
#                 MaxNumberOfMessages=1,  
#                 WaitTimeSeconds=10       
#             )
#             if 'Messages' in response:
#                 message = response['Messages'][0]
#                 message_body = message['Body']
#                 receipt_handle = message['ReceiptHandle']

#                 logger.info(f"Message sent to SQS: {response['MessageId']}")
#                 # sqs.delete_message(
#                 #     QueueUrl='https://sqs.us-east-1.amazonaws.com/226211702586/dev_resume_processor.fifo',
#                 #     ReceiptHandle=receipt_handle
#                 # )
#                 # print("Message deleted from the queue.")
#                 return message_body
#             else:
#                 logger.info("No messages in the queue.")
#                 return None

#         except Exception as e:
#             logger.exception("Error receiving message from SQS.")
#             return None

#     @log_function_call
#     def get(self, request):
#         try:
#             logger.info("Received GET request for questions.")
#             message = self.receive_message_from_sqs()
#             if message:
#                 logger.info(f"Received message from SQS: {message}")
#                 return JsonResponse({'message': message}, status=200)
#             else:
#                 logger.info("No messages in the SQS queue.")
#                 return JsonResponse({'message': 'No messages in the queue'}, status=200)
#         except Exception as e:
#             logger.exception("Error occurred while processing GET request.")
#             return JsonResponse({'error': 'An error occurred while retrieving the message.'}, status=500)

#     @log_function_call 
#     def post(self, request):
#         try:
#             logger.info("Received POST request to generate questions.")
#             vector_db = connect_to_vectorDB("interview_questions")
#             # job_id = request.data.get('job_id')
#             # candidate_id = request.data.get('candidate_id')
#             schedule_id = request.data.get('schedule_id')
#             # message = self.receive_message_from_sqs()
#             # if message is None:
#             #     return JsonResponse({'error': 'No messages in the queue'}, status=400)
#             # candidate_id = message.get('candidate_id')
#             # job_id = message.get('job_id')
    
#             schedule = get_object_or_404(InterviewSchedule, pk=schedule_id)
#             # Get candidate and job from the fetched schedule
#             candidate = schedule.candidate
#             job = schedule.job
#             job_id = job.id
#             candidate_id = candidate.id

#             if not job_id:
#                 return JsonResponse({'error': 'Job ID is required'}, status=400)

#             if not candidate_id:
#                 return JsonResponse({'error': 'Candidate ID is required'}, status=400)

#             # Fetch JobPosting and Candidate based on input
#             job = get_object_or_404(JobPosting, pk=job_id)
#             candidate = get_object_or_404(Candidate, pk=candidate_id)  # Use 'pk' for candidate_id
#             schedule = get_object_or_404(InterviewSchedule, pk=schedule_id)

#             job_description = job.job_description
#             job_title = job.job_header

#             # resume_file = request.FILES.get('resume')
#             # if not resume_file:
#                 # logger.info("No resume file provided")
#             #     return JsonResponse({'error': 'No resume file provided'}, status=400)
        
#             static_resume_path = os.path.join(settings.BASE_DIR, r'static\files\data_scientist_resume.xlsx')
#             resume_file = open(static_resume_path, 'rb')
#             # Process the resume and generate questions in the background
#             threading.Thread(target=self.generate_questions, args=(candidate, job, job_title, resume_file, job_description,schedule, vector_db)).start()

#             return JsonResponse({'message': 'Questions are being generated', 'job_id': job.id, 'candidate_id': candidate.id,'schedule':schedule.id}, status=201)
#         except Exception as e:
#             logger.exception("Error occurred while processing POST request.")
#             return JsonResponse({'error': 'An error occurred while generating the questions.'}, status=500)
#     @log_function_call  
#     def generate_questions(self, candidate, job, job_title, resume_file, job_description,schedule, vector_db):
#         try:
#             logger.info(f"Starting question generation for Candidate ID: {candidate.id}, Job Title: {job_title}")
#             resume_filename = secure_filename(resume_file.name)
#             resume_filename = os.path.splitext(resume_filename)[0]
#             message_body = {
#                 "candidate_id": candidate.id,
#                 "job_id": job.id,
#                 "resume_filename": resume_filename,
#             }
#             message_body_str = str(message_body)
#             # self.send_message_to_sqs(message_body_str, 'resume_processor')

#             resume_text = extract_text_from_file(resume_file)
#             print("Ffffffffffff",resume_text)
#             resume_skills = extract_skills(resume_text)
#             experience = cal_experience(resume_text)
#             job_skills = extract_skills(job_description)
#             matched_skills = match_skills(resume_skills, job_skills)
#             if not matched_skills:
#                 matched_skills = normalize_skills(job_skills)
#             logger.info(f"Matched skills for Candidate ID: {candidate.id}: {matched_skills}")
#             all_questions = []
#             questions = []

#             def process_skill(skill):
#                 try:
#                     nonlocal questions, all_questions
#                     questions_data = generate_interview_questions([skill],matched_skills,experience, num_questions=5, vector_db=vector_db)
#                     for question_text in questions_data.get(skill, []):
#                         # Save each question into BotJobCandidateQuestion model
#                         question_entry = BotJobCandidateQuestion.objects.create(
#                             tenant=candidate.tenant,  # assuming tenant is a shared field between Candidate and JobPosting
#                             job=job,
#                             candidate=candidate,
#                             schedule=schedule,
#                             bot_question_source=1,  
#                             question=question_text,
#                             active=1,
#                             deleted=0,
#                             updated_by=1,  
#                         )
#                         questions.append(question_text)
#                         all_questions.append(question_entry.question)
#                         logger.info(f"Processed skill {skill} for Candidate ID: {candidate.id} question:{question_text}")

#                 except Exception as e:
#                     logger.exception(f"Error processing skill {skill} for Candidate ID: {candidate.id}")
#             threads = []

#             # Create threads for each skill to process them concurrently
#             for skill in matched_skills:
#                 thread = threading.Thread(target=process_skill, args=(skill,))
#                 threads.append(thread)
#                 thread.start()

#             # Wait for all threads to finish
#             for thread in threads:
#                 thread.join()

#             if questions:
#                 save_questions_to_vectorDB(questions)
#                 vector_db.persist()

#             return all_questions
#         except Exception as e:
#             logger.exception(f"Error occurred during question generation for Candidate ID: {candidate.id}")


import base64
import PyPDF2
class QuestionsView(APIView):
    permission_classes = [AllowAny]
    @log_function_call
    def extract_text_from_blob(self, pdf_data):
        if isinstance(pdf_data, str):
            pdf_bytes = base64.b64decode(pdf_data)
        else:
            pdf_bytes = pdf_data
        temp_pdf_path = 'temp_file.pdf'
        with open(temp_pdf_path, 'wb') as f:
            f.write(pdf_bytes)
        # print("dszfffvzc",pdf_bytes)
        with open(temp_pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            
            for page in pdf_reader.pages:
                text += page.extract_text() if page.extract_text() else ''
                
        # print(text,"dddddddd")
        return text

    @log_function_call 
    def post(self, request):
        try:
            logger.info("Received POST request to generate questions.")
            schedule_id = request.data.get('schedule_id')

            result = self.generate_questions_helper(schedule_id)
            return JsonResponse(result, status=201)

        except Exception as e:
            logger.exception("Error occurred while processing POST request.")
            return JsonResponse({'error': 'An error occurred while generating the questions.'}, status=500)
    @log_function_call 
    def generate_questions_helper(self,schedule_id):
        try:
            logger.info("Generating questions.")
            # Fetch necessary objects
            vector_db = connect_to_vectorDB("interview_questions")
            schedule = get_object_or_404(InterviewSchedule, pk=schedule_id)
            candidate = schedule.candidate
            job = schedule.job
            resume=schedule.resume
            job_id = job.id
            candidate_id = candidate.id
            resume_id = resume.id
            if not job_id:
                return JsonResponse({'error': 'Job ID is required'}, status=400)

            if not candidate_id:
                return JsonResponse({'error': 'Candidate ID is required'}, status=400)

            job = get_object_or_404(JobPosting, pk=job_id)
            candidate = get_object_or_404(Candidate, pk=candidate_id)
            resume=get_object_or_404(Resume,pk=resume_id)
            # schedule = get_object_or_404(InterviewSchedule, pk=schedule_id)

            job_description = job.job_description
            job_title = job.job_header
            
            if not resume:
                return JsonResponse({'error': 'No active resume found for candidate'}, status=404)
            logger.debug(f"Resume content type: {type(resume.content)}")

            if resume.type == 'application/pdf':
                resume_text = self.extract_text_from_blob(resume.content)  # Assuming `content` field stores BLOB
                if resume_text is None:
                    return JsonResponse({'error': 'Failed to extract text from resume PDF BLOB'}, status=500)
        
            # print(resume,"duhnihji")
            # static_resume_path = os.path.join(settings.BASE_DIR, r'static\files\data_scientist_resume.xlsx')
            # resume_file = open(static_resume_path, 'rb')
            # Start question generation process
            threading.Thread(target=self.generate_questions, args=(candidate, job, job_title, resume_text, job_description, schedule, vector_db)).start()
            return {'message': 'Questions are being generated', 'job_id': job.id, 'candidate_id': candidate.id, 'schedule': schedule.id}
        
        except Exception as e:
            logger.exception("Error generating questions.")
            return {'error': 'An error occurred while generating questions'}
    @log_function_call 
    def generate_questions(self, candidate, job, job_title, resume_text, job_description, schedule, vector_db):
        try:
            logger.info(f"Starting question generation for Candidate ID: {candidate.id}, Job Title: {job_title}")
            # resume_filename = secure_filename(resume_file.name)
            # resume_filename = os.path.splitext(resume_filename)[0]
            # resume_text = extract_text_from_file(resume_file)
            # resume_text=resume_file
            resume_skills = extract_skills(resume_text)
            experience = cal_experience(resume_text)
            job_skills = extract_skills(job_description)
            matched_skills = match_skills(resume_skills, job_skills)
            if not matched_skills:
                matched_skills = normalize_skills(job_skills)
            logger.info(f"Matched skills for Candidate ID: {candidate.id}: {matched_skills}")
            all_questions = []
            questions = []

            def process_skill(skill):
                try:
                    nonlocal questions, all_questions
                    questions_data = generate_interview_questions([skill],matched_skills,experience, num_questions=5, vector_db=vector_db)
                    for question_text in questions_data.get(skill, []):
                        # Save each question into BotJobCandidateQuestion model
                        question_entry = BotJobCandidateQuestion.objects.create(
                            tenant=candidate.tenant,  # assuming tenant is a shared field between Candidate and JobPosting
                            job=job,
                            candidate=candidate,
                            schedule=schedule,
                            bot_question_source=1,  
                            question=question_text,
                            active=1,
                            deleted=0,
                            updated_by=1,  
                        )
                        questions.append(question_text)
                        all_questions.append(question_entry.question)
                        logger.info(f"Processed skill {skill} for Candidate ID: {candidate.id} question:{question_text}")

                except Exception as e:
                    logger.exception(f"Error processing skill {skill} for Candidate ID: {candidate.id}")
            threads = []

            # Create threads for each skill to process them concurrently
            for skill in matched_skills:
                thread = threading.Thread(target=process_skill, args=(skill,))
                threads.append(thread)
                thread.start()

            # Wait for all threads to finish
            for thread in threads:
                thread.join()

            if questions:
                save_questions_to_vectorDB(questions)
                vector_db.persist()

            return all_questions
        except Exception as e:
            logger.exception(f"Error occurred during question generation for Candidate ID: {candidate.id}")
