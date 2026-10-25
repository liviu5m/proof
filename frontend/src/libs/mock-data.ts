export const mockDatasets = [
  {
    id: "ds_1",
    name: "Customer Support QA Set",
    item_count: 250,
    hash: "a1b2c3d4e5f67890",
    createdAt: new Date().toISOString(),
  },
  {
    id: "ds_2",
    name: "Code Generation Benchmarks",
    item_count: 120,
    hash: "f6e5d4c3b2a10987",
    createdAt: new Date().toISOString(),
  },
];

export const mockRuns = [
  {
    id: "run_901",
    datasetName: "Customer Support QA Set",
    model: "gemini-3.5-flash-lite",
    score: 4.8,
    status: "Completed",
    itemsEvaluated: 250,
    createdAt: "2026-10-25 14:10:00",
    results: [
      { id: 1, prompt: "How do I reset my password?", response: "Click forgot password on login page...", score: 5, reasoning: "Clear and accurate." },
      { id: 2, prompt: "What is your refund policy?", response: "Refunds are issued within 30 days...", score: 4.5, reasoning: "Mostly correct, missing minor details." },
    ]
  },
  {
    id: "run_902",
    datasetName: "Code Generation Benchmarks",
    model: "gemini-3.5-flash-lite",
    score: 4.2,
    status: "Completed",
    itemsEvaluated: 120,
    createdAt: "2026-10-25 12:00:00",
    results: [
      { id: 1, prompt: "Write a quicksort in Python", response: "def quicksort(arr): ...", score: 4.5, reasoning: "Efficient implementation." },
      { id: 2, prompt: "Reverse a linked list", response: "class Node: ...", score: 4.0, reasoning: "Correct pointer manipulation." },
    ]
  }
];
