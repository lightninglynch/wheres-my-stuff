# Where's My Stuff

Ask Alexa where you left your phone, keys, wallet, or charger. A laptop webcam runs an open-vocabulary detector, posts last-seen locations to AWS, and the Alexa skill reads them back in plain speech.

```
Webcam --> YOLO-World detector --> POST /track (API key) --> DynamoDB
Alexa  --> skill Lambda ------------------------------------^
```

The default COCO YOLO model cannot see wallet, keys, or a charger. This project uses **YOLO-World** (`yolov8s-worldv2.pt`) so those classes are set at runtime. Open-vocab models are weaker than a custom-trained detector on small far-away objects — put the camera at desk height, pointed at the table or hook where things actually land.

Tracked items: wallet, keys, charger, phone, remote, glasses, headphones.

Landmarks used for “near the …”: couch, chair, table, lamp, tv, laptop, bottle, backpack.

## 1. Deploy the AWS backend

You need an AWS account and the [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html). Use **us-east-1** so the Alexa skill Lambda is in a region Alexa can call.

```bash
sam build
sam deploy --guided --region us-east-1
```

`sam build` uses the repo `Makefile` so only the Lambda handlers and `shared/` are packaged — not the detector venv or YOLO weights.

Accept the defaults, then copy these stack outputs:

- `TrackApiUrl` — detector `API_ENDPOINT`
- `TrackApiKeyId` — fetch the secret value:

```bash
aws apigateway get-api-key --api-key KEY_ID --include-value --query value --output text
```

- `AlexaSkillFunctionArn` — Alexa endpoint

If the table name `ObjectLocations` already exists in the account, either delete it or change `TableName` in `template.yaml` before deploying.

## 2. Run the detector

Python 3.10+ and a webcam.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r detector/requirements.txt
cp detector/.env.example detector/.env
```

Edit `detector/.env` with `API_ENDPOINT` and `API_KEY`. Then from the repo root:

```bash
python detector/tracker.py
```

The first run downloads `yolov8s-worldv2.pt`. A window labeled **Object Finder** shows boxes (green = tracked item, gray = landmark). Press `q` to quit.

Writes are debounced: a location is posted on first sighting, when nearby objects change, or every 20 seconds — not every frame. If the object leaves the frame, the last DynamoDB record is kept so Alexa can still say “I last saw …”.

If `API_ENDPOINT` is empty, the detector still runs and logs payloads instead of posting. That is enough to confirm the camera and model work.

Smoke test: hold up a phone so it is boxed in the window, then check CloudWatch or DynamoDB for a `phone` item.

## 3. Connect Alexa

1. In the [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask), create a custom skill named **Object Finder**.
2. Set the invocation name to `object finder` (already in `alexa_skill/skill.json`).
3. Paste the contents of `alexa_skill/skill.json` into **Build → Interaction Model → JSON Editor** and save/build the model.
4. Under **Build → Endpoint**, choose **AWS Lambda ARN** and paste `AlexaSkillFunctionArn`.
5. Copy the skill ID (`amzn1.ask.skill...`) from the developer console.
6. Redeploy so the Lambda verifies that ID:

```bash
sam deploy --parameter-overrides AlexaSkillId=amzn1.ask.skill.YOUR_ID --region us-east-1
```

7. Enable the skill in the Alexa app on the same Amazon account as your Echo.

Try:

- “Alexa, open object finder”
- “Alexa, ask object finder where my phone is”
- “Alexa, ask object finder what have you seen”

Answers use relative time (“about 5 minutes ago”) and landmarks when the detector saw them (“near the lamp”).

## Tests

From the repo root (no AWS or camera required):

```bash
python -m unittest discover -s tests -v
```
