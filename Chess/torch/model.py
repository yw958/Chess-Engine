import torch
import torch.nn as nn


class ChessModel(nn.Module):
    def __init__(self, in_channels=18):
        super(ChessModel, self).__init__()
        # Shared board encoder.
        self.conv1 = nn.Conv2d(in_channels, 64, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.flatten = nn.Flatten()
        self.fc1 = nn.Linear(8 * 8 * 128, 256)
        self.move_head = nn.Linear(256, 64 * 64)
        self.relu = nn.ReLU()

        # Initialize weights.
        nn.init.kaiming_uniform_(self.conv1.weight, nonlinearity="relu")
        nn.init.kaiming_uniform_(self.conv2.weight, nonlinearity="relu")
        nn.init.xavier_uniform_(self.fc1.weight)
        nn.init.xavier_uniform_(self.move_head.weight)

    @staticmethod
    def apply_legal_mask(logits, legal_mask):
        if legal_mask is None:
            return logits
        legal_mask = legal_mask.to(device=logits.device, dtype=torch.bool).reshape(logits.size(0), -1)
        return logits.masked_fill(~legal_mask, -1e9)

    def forward(self, x, legal_mask=None):
        x = self.relu(self.conv1(x))
        x = self.relu(self.conv2(x))
        x = self.flatten(x)
        x = self.relu(self.fc1(x))

        move_logits = self.move_head(x)
        move_logits = self.apply_legal_mask(move_logits, legal_mask)

        return move_logits
