# Tasks for Tomorrow

## 1. Complete Image Creator Deployment
- [ ] Finish deployment to droplet (follow DEPLOY_TO_DROPLET.md)
- [ ] Test Image Creator at `tools.lemauricienltd.com/image_creator`
- [ ] Verify all features work correctly

## 2. Setup Google OAuth
- [ ] Go to [Google Cloud Console](https://console.cloud.google.com/)
- [ ] Create/select project
- [ ] Enable Google+ API
- [ ] Create OAuth 2.0 credentials
- [ ] Add authorized redirect URI: `https://tools.lemauricienltd.com/auth/google/callback`
- [ ] Copy Client ID and Secret
- [ ] Update `.env` file on droplet with:
  - `GOOGLE_CLIENT_ID`
  - `GOOGLE_CLIENT_SECRET`
- [ ] Restart image-creator service: `sudo systemctl restart image-creator`
- [ ] Test Google OAuth login

## 3. Implement Bulk Watermarking
- [ ] Review current watermarking functionality
- [ ] Design bulk watermarking feature:
  - [ ] UI for selecting multiple images
  - [ ] Batch processing logic
  - [ ] Progress indicator
  - [ ] Download all watermarked images (zip file?)
- [ ] Implement bulk watermarking feature
- [ ] Test with multiple images
- [ ] Deploy and test on production

## Notes
- Current deployment location: `/opt/image-creator/`
- Service runs as `www-data` user
- Port: 8000
- Nginx config: Add to `/etc/nginx/sites-available/tracking-server`
