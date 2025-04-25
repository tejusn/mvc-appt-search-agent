# How to Schedule a Cloud Function on Google Cloud Platform (GCP)

This guide explains how to set up a Cloud Function on GCP that runs on a schedule using Cloud Scheduler and Pub/Sub.

## Overview

To run a Cloud Function on schedule, we'll use three GCP services:
1. **Cloud Functions** - The serverless code that will execute
2. **Pub/Sub** - Message broker that connects Cloud Scheduler to your function
3. **Cloud Scheduler** - Service that triggers events on a schedule

## Step 1: Create a Cloud Function with Pub/Sub Trigger

1. Go to the Google Cloud Console
2. Navigate to Cloud Functions
3. Click "CREATE FUNCTION"
4. Configure your function:
   - **Environment**: 1st gen or 2nd gen (2nd gen recommended for newer projects)
   - **Function name**: Choose a descriptive name
   - **Region**: Select your preferred region
   - **Trigger type**: Select "Cloud Pub/Sub"
   - **Cloud Pub/Sub topic**: Create a new topic (e.g., "function-trigger-topic")
   - **Runtime**: Choose your preferred runtime (e.g., Node.js, Python, Go, etc.)

5. Write your function code that processes the Pub/Sub message
   - For Python, implement a function that accepts `event` and `context` parameters
   - For Node.js, implement a function that accepts `message` and `context` parameters

## Step 2: Create an Eventarc Trigger (Alternative Approach)

If you're using Cloud Run functions (2nd gen), you can use Eventarc triggers:

1. Go to Cloud Functions and create/edit your function
2. Under "Trigger" section, select "Eventarc trigger"
3. Configure the trigger:
   - **Event provider**: Select "Pub/Sub"
   - **Event type**: Choose "google.cloud.pubsub.topic.v1.messagePublished"
   - **Pub/Sub topic**: Create or select your topic

## Step 3: Set Up Cloud Scheduler

1. Go to the Google Cloud Console
2. Navigate to "Cloud Scheduler"
3. Click "CREATE JOB"
4. Configure the scheduler job:
   - **Name**: Give your job a descriptive name
   - **Region**: Choose the same region as your function
   - **Frequency**: Enter a cron expression for your schedule
     - Example: `0 * * * *` (every hour)
     - Example: `0 0 * * *` (daily at midnight)
     - Example: `*/10 * * * *` (every 10 minutes)
   - **Timezone**: Select your preferred timezone
5. Set the target:
   - **Target type**: Select "Pub/Sub"
   - **Topic**: Choose the Pub/Sub topic you created earlier
   - **Message body**: Add a simple JSON message like `{"message": "scheduled-trigger"}`

6. Click "CREATE" to save and activate your scheduler job

## Custom Scheduling Example

To run a function every minute but only between 2:30 AM and 4:00 AM, create two Cloud Scheduler jobs:

**Job 1 (2:30 AM - 2:59 AM):**
```
30-59 2 * * *
```

**Job 2 (3:00 AM - 3:59 AM):**
```
0-59 3 * * *
```

Both jobs should target the same Pub/Sub topic to trigger the same Cloud Function.

## Troubleshooting

If your Cloud Function or Cloud Run service shows an error like:
```
service: projects/[PROJECT-ID]/locations/[REGION]/services/[SERVICE-NAME], in region: [REGION] is not ready: failed precondition
```

Check the following:
1. Service deployment status in the Cloud Console
2. Deployment and container logs for error messages
3. Service configuration (memory, CPU, environment variables)
4. IAM permissions for your account
5. Wait a few minutes and retry the operation

## Cost Considerations

- Cloud Functions: Charged based on invocations, compute time, and memory usage
- Pub/Sub: Charged based on data volume
- Cloud Scheduler: Free tier includes 3 jobs, then $0.10 per job per month

## Best Practices

1. Use meaningful names for your Cloud Scheduler jobs and Pub/Sub topics
2. Include relevant metadata in your Pub/Sub messages if your function needs specific information
3. Set appropriate timeouts and memory allocations for your functions
4. Use error handling in your function code to handle failed executions
5. Set up monitoring and alerts for failed function executions
