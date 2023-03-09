FROM public.ecr.aws/lambda/python:3.8

# Install gcc compiler
RUN yum install gcc -y

# Copy function code
COPY lambda_function.py ${LAMBDA_TASK_ROOT}
COPY supporting_functions.py ${LAMBDA_TASK_ROOT}

# Install the function's dependencies using file requirements.txt
# from your project folder.
COPY requirements.txt  .
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Add configs for landscape and great expectations
COPY project_config.yml ${LAMBDA_TASK_ROOT}
ADD great_expectations ${LAMBDA_TASK_ROOT}/great_expectations

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "lambda_function.lambda_handler" ] 