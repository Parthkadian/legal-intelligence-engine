import torch
from transformers import BertTokenizer, BertForSequenceClassification
from torch.utils.data import Dataset, DataLoader

class LegalDataset(Dataset):
    def __init__(self, texts, labels, tokenizer):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        encoding = self.tokenizer(
            self.texts[idx],
            padding='max_length',
            truncation=True,
            max_length=256,
            return_tensors="pt"
        )
        return {
            'input_ids': encoding['input_ids'].squeeze(),
            'attention_mask': encoding['attention_mask'].squeeze(),
            'label': torch.tensor(self.labels[idx])
        }

def train_model(texts, labels):
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    dataset = LegalDataset(texts, labels, tokenizer)
    loader = DataLoader(dataset, batch_size=8, shuffle=True)

    model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=5)

    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)

    model.train()
    for epoch in range(3):
        for batch in loader:
            outputs = model(
                input_ids=batch['input_ids'],
                attention_mask=batch['attention_mask'],
                labels=batch['label']
            )
            loss = outputs.loss
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()

    model.save_pretrained("models/bert_model")
    tokenizer.save_pretrained("models/bert_model")
if __name__ == "__main__":
    texts = [
        "This agreement is made between two parties",
        "The court finds the defendant guilty",
        "This is a legal notice regarding property",
        "This contract is legally binding",
        "Patent application for invention"
    ]

    labels = [3, 1, 2, 0, 4]

    train_model(texts, labels)