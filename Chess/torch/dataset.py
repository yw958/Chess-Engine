from torch.utils.data import Dataset


class ChessDataset(Dataset):

    def __init__(self, X, y, legal_masks):
        self.X = X
        self.y = y
        self.legal_masks = legal_masks

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return (
            self.X[idx],
            self.y[idx],
            self.legal_masks[idx],
        )
