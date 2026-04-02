import json
import torch
from torch.utils.data import Dataset
from transformers import AutoTokenizer

class InterviewDataset(Dataset):
    def __init__(self, data_path, tokenizer_name="roberta-base", max_length=512):
        with open(data_path, "r") as f:
            self.data = json.load(f)
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        self.max_length = max_length

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        question = item["question"]
        answer = item["answer"]
        score = float(item["score"])

        encoding = self.tokenizer(
            question,
            answer,
            padding="max_length",
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt"
        )

        return {
            "input_ids": encoding["input_ids"].flatten(),
            "attention_mask": encoding["attention_mask"].flatten(),
            "labels": torch.tensor(score, dtype=torch.float)
        }
