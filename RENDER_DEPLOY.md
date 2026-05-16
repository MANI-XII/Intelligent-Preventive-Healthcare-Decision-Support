# Render Deployment Guide

This project is prepared for deployment on Render with:

- `preventive-health-api` as a Python web service
- `preventive-health-frontend` as a Next.js web service
- `preventive-health-db` as a managed Postgres database

## Files added

- [render.yaml](/Users/edulapurammanikanta/PROJECT_PHASE-2_UPDATED/render.yaml)

## Before deploying

Make sure your repository is pushed to GitHub, GitLab, or Bitbucket.

## Deploy steps

1. Log in to [Render](https://render.com/).
2. Click `New` -> `Blueprint`.
3. Connect the repository that contains this project.
4. Render will detect `render.yaml` at the repo root.
5. Review the three resources it plans to create:
   - `preventive-health-db`
   - `preventive-health-api`
   - `preventive-health-frontend`
6. Add your AI key in the backend service settings after creation:
   - for OpenAI: `OPENAI_API_KEY`
   - for Gemini: `GEMINI_API_KEY`
   - for xAI/Grok: `XAI_API_KEY`
7. Apply the blueprint and wait for the deploy to finish.

## Important notes

- The backend CORS origin is preset to `https://preventive-health-frontend.onrender.com`.
- The frontend API base URL is preset to `https://preventive-health-api.onrender.com`.
- If you rename either Render service, update both values in `render.yaml`.
- The backend uses Render Postgres through `POSTGRES_URL`.
- `JWT_SECRET_KEY` is generated automatically by Render from the blueprint.

## Health checks

- Backend health endpoint: `/health`
- Frontend root path: `/`

## Official references

- [Render Blueprint spec](https://render.com/docs/blueprint-spec)
- [Render monorepo support](https://render.com/docs/monorepo-support)
- [Render web services](https://render.com/docs/web-services)
