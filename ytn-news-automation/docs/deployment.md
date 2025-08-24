### Cloud Run Deployment (FastAPI)

Prereqs:
- gcloud CLI authenticated and configured for your project
- Firestore in Native mode in the same project
- `config/serviceAccountKey.json` available (mounted or baked)

Local test:
```
pip install -r server/requirements.txt
uvicorn server.main:app --host 0.0.0.0 --port 8080
```

Build & Deploy:
```
gcloud builds submit --tag gcr.io/$PROJECT_ID/ytn-news-api ./ytn-news-automation
gcloud run deploy ytn-news-api \
  --image gcr.io/$PROJECT_ID/ytn-news-api \
  --platform managed \
  --region asia-northeast3 \
  --allow-unauthenticated \
  --set-env-vars FIREBASE_PROJECT_ID=$PROJECT_ID \
  --set-env-vars GOOGLE_APPLICATION_CREDENTIALS=config/serviceAccountKey.json
```

Note: Ensure the container includes `config/serviceAccountKey.json`. For production, prefer Workload Identity over keys.






