# API Contract

This document records the planned AnytimeSpeak MVP API shape for future frontend and backend integration. The current backend only implements `/api/health`; the other endpoints can be implemented in mock mode first so local demos remain reproducible without private API keys.

## General Rules

- Base path: `/api`
- Request and response bodies use JSON.
- Mock mode is acceptable for all MVP endpoints until provider integration is added.
- Mock responses should be deterministic enough for demo recording.
- API keys, provider tokens, and `.env` contents must never be returned to the frontend.
- Error responses should use a predictable shape:

```json
{
  "error": {
    "code": "invalid_request",
    "message": "scenarioId is required."
  }
}
```

## GET /api/health

Checks whether the backend service is running.

Current status: implemented.

### Response Example

```json
{
  "status": "ok"
}
```

## GET /api/scenarios

Returns the scenario list shown by the frontend. The MVP scenarios should appear first: Interview, Restaurant Ordering, and Meeting. Additional scenarios can be included after the stable MVP path is complete.

Current status: planned. Can be implemented with static mock data first.

### Response Example

```json
{
  "scenarios": [
    {
      "id": "interview",
      "title": "Interview",
      "titleZh": "面试",
      "level": "Intermediate",
      "aiRole": "Hiring manager",
      "userRole": "Job candidate",
      "goal": "Practice introducing yourself, explaining experience, and asking professional follow-up questions.",
      "openingLine": "Hi, thanks for joining today. Could you briefly introduce yourself and tell me why you are interested in this role?"
    },
    {
      "id": "restaurant-ordering",
      "title": "Restaurant Ordering",
      "titleZh": "点餐",
      "level": "Beginner to Intermediate",
      "aiRole": "Restaurant server",
      "userRole": "Customer",
      "goal": "Practice ordering food, asking for recommendations, clarifying preferences, and confirming the order.",
      "openingLine": "Welcome! Are you ready to order, or would you like a few recommendations first?"
    },
    {
      "id": "meeting",
      "title": "Meeting",
      "titleZh": "会议",
      "level": "Intermediate",
      "aiRole": "Team lead",
      "userRole": "Team member",
      "goal": "Practice giving updates, discussing blockers, asking for clarification, and agreeing on next steps.",
      "openingLine": "Let's start with your update. What progress have you made since our last meeting?"
    }
  ]
}
```

## POST /api/chat

Sends a user message and receives the next role-play reply. The endpoint can also return brief per-turn feedback when there is a clear grammar or expression issue.

Current status: planned. Can return mock role-play replies based on `scenarioId`.

### Request Example

```json
{
  "sessionId": "demo-session-001",
  "scenarioId": "interview",
  "messages": [
    {
      "id": "msg-001",
      "role": "assistant",
      "content": "Hi, thanks for joining today. Could you briefly introduce yourself and tell me why you are interested in this role?"
    },
    {
      "id": "msg-002",
      "role": "user",
      "content": "I worked in a team project before and I was responsible to build the frontend page."
    }
  ],
  "mode": "mock"
}
```

### Response Example

```json
{
  "sessionId": "demo-session-001",
  "message": {
    "id": "msg-003",
    "role": "assistant",
    "content": "Thanks for sharing that. Could you tell me more about the frontend work and how it helped the project?"
  },
  "quickFeedback": {
    "grammar": {
      "original": "responsible to build",
      "suggestion": "responsible for building",
      "reason": "After responsible for, use a noun or gerund form."
    },
    "expression": {
      "original": "frontend page",
      "suggestion": "frontend interface",
      "reason": "Frontend interface sounds more natural when describing product work."
    },
    "encouragement": "Your answer is relevant to the interview scenario."
  },
  "isMock": true
}
```

## POST /api/feedback

Generates grammar and expression feedback for a specific user message or a recent group of turns. This endpoint is useful if the frontend wants feedback separately from the chat reply.

Current status: planned. Can use mock rules before AI provider integration.

### Request Example

```json
{
  "sessionId": "demo-session-001",
  "scenarioId": "interview",
  "messageId": "msg-002",
  "content": "I worked in a team project before and I was responsible to build the frontend page.",
  "mode": "mock"
}
```

### Response Example

```json
{
  "messageId": "msg-002",
  "feedback": {
    "grammar": [
      {
        "original": "responsible to build",
        "suggestion": "responsible for building",
        "reason": "Use responsible for plus a noun or gerund."
      }
    ],
    "expression": [
      {
        "original": "frontend page",
        "suggestion": "frontend interface",
        "reason": "This phrase sounds more natural in a professional interview answer."
      }
    ],
    "encouragement": "The meaning is clear, and the example fits the interview goal."
  },
  "isMock": true
}
```

## POST /api/summary

Ends or reviews a practice session and returns a post-session summary with scores. The frontend can call this after the user selects the end-practice action.

Current status: planned. Can calculate deterministic mock scores first.

### Request Example

```json
{
  "sessionId": "demo-session-001",
  "scenarioId": "interview",
  "messages": [
    {
      "id": "msg-001",
      "role": "assistant",
      "content": "Hi, thanks for joining today. Could you briefly introduce yourself and tell me why you are interested in this role?"
    },
    {
      "id": "msg-002",
      "role": "user",
      "content": "I worked in a team project before and I was responsible to build the frontend page."
    },
    {
      "id": "msg-003",
      "role": "assistant",
      "content": "Thanks for sharing that. Could you tell me more about the frontend work and how it helped the project?"
    }
  ],
  "mode": "mock"
}
```

### Response Example

```json
{
  "sessionId": "demo-session-001",
  "summary": {
    "overallPerformance": "You gave a relevant answer and connected your experience to the interview scenario. Your next step is to make the wording more professional and add a clearer result from the project.",
    "strengths": [
      "You answered the interview question directly.",
      "You used a concrete project example."
    ],
    "repeatedIssues": [
      "Preposition use after phrases such as responsible for.",
      "Some wording can be more natural for professional settings."
    ],
    "betterExpressions": [
      "I was responsible for building the frontend interface.",
      "I contributed to a team project focused on user experience.",
      "This helped our team present the product more clearly."
    ],
    "scenarioCompletion": "The learner introduced relevant project experience. A stronger answer would include the project result and one professional follow-up question.",
    "nextPracticeFocus": "Practice describing one project with action, result, and reflection."
  },
  "scores": {
    "grammar": 78,
    "expression": 76,
    "fluency": 80,
    "scenarioCompletion": 72,
    "overall": 76
  },
  "scoreScale": "0-100",
  "isMock": true
}
```

## Endpoint Implementation Order

1. Keep `/api/health` as the smoke test endpoint.
2. Add `/api/scenarios` with static scenario data.
3. Add `/api/chat` with deterministic mock role-play replies.
4. Add `/api/feedback` if feedback is separated from chat responses.
5. Add `/api/summary` with mock summaries and scores.
6. Replace mock internals with provider-backed logic only after the mock demo loop is stable.
