FROM tensorflow/serving

WORKDIR /models_api

ADD . /models_api

EXPOSE 8501

ENTRYPOINT ["tensorflow_model_server", "--model_config_file=/models_api/model_config.conf"]

CMD ["--rest_api_port=8501"]
