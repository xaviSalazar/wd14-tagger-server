FROM python:3.9-slim
# Install wget and other dependencies
RUN apt-get update && apt-get install -y wget libgl1-mesa-glx libglib2.0-0 && rm -rf /var/lib/apt/lists/*
WORKDIR /usr/src/app
COPY . .
RUN mkdir /usr/src/app/models
WORKDIR /usr/src/app/models
RUN wget https://huggingface.co/SmilingWolf/wd-swinv2-tagger-v3/resolve/main/model.onnx --content-disposition -O wd-swinv2-tagger-v3.onnx
RUN wget https://huggingface.co/SmilingWolf/wd-swinv2-tagger-v3/resolve/main/selected_tags.csv --content-disposition -O wd-swinv2-tagger-v3.csv
WORKDIR /usr/src/app/
RUN cp .env.exp .env
RUN sed -i 's|SERVER_HOST=127.0.0.1|SERVER_HOST=0.0.0.0|' .env
RUN apt-get update && apt-get install -y libgl1-mesa-glx libglib2.0-0 && rm -rf /var/lib/apt/lists/*
RUN pip install pdm
RUN pdm install
EXPOSE 5010
CMD ["pdm", "run", "python3", "main.py"]