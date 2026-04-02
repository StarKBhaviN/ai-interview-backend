import os
from transformers import (
    AutoModelForSequenceClassification, 
    TrainingArguments, 
    Trainer, 
    DataCollatorWithPadding, 
    AutoTokenizer
)
from .dataset import InterviewDataset

def fine_tune():
    """
    Main function to fine-tune RoBERTa-base on the provided training data.
    The model is trained as a regressor (num_labels=1) using Mean Squared Error.
    """
    # 1. Setup paths
    base_path = os.path.dirname(__file__)
    data_path = os.path.join(base_path, "data/training_data.json")
    output_dir = os.path.join(base_path, "checkpoints/relevance_model")

    # 2. Load Dataset and Tokenizer
    tokenizer = AutoTokenizer.from_pretrained("roberta-base")
    dataset = InterviewDataset(data_path, tokenizer_name="roberta-base")

    # 3. Load Model with Regression Config
    model = AutoModelForSequenceClassification.from_pretrained(
        "roberta-base", 
        num_labels=1
    )

    # 4. Define Training Arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=5,
        per_device_train_batch_size=8,
        learning_rate=2e-5,
        weight_decay=0.01,
        save_strategy="epoch",
        logging_steps=10,
        remove_unused_columns=False,
        push_to_hub=False,
        fp16=False # Set to True if using GPU with FP16 support
    )

    # 5. Initialize Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        data_collator=DataCollatorWithPadding(tokenizer),
    )

    # 6. Train and Save
    print(f"Starting training on {len(dataset)} examples...")
    trainer.train()
    trainer.save_model(output_dir)
    print(f"Training complete. Model saved to {output_dir}")

if __name__ == "__main__":
    fine_tune()
