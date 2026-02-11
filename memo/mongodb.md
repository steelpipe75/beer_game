# Docker で MongoDB を起動

```bash
docker run -d --name mongo -p 27017:27017 -v mongo-data:/data/db mongo:7
```
