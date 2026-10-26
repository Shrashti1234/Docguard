"""Pretrained MiT-B0 encoder with a small multiscale binary segmentation decoder."""
import torch
from pathlib import Path
from huggingface_hub import try_to_load_from_cache
from torch import nn
from transformers import SegformerConfig, SegformerModel


class TransformerSegmenter(nn.Module):
    def __init__(self, pretrained='nvidia/mit-b0', encoder_config=None, freeze_encoder=False):
        super().__init__()
        self.pretrained_revision = None
        if encoder_config is None:
            self.encoder, loading = SegformerModel.from_pretrained(pretrained, output_loading_info=True)
            missing = loading.get('missing_keys', [])
            if missing or loading.get('mismatched_keys'):
                raise RuntimeError(f'Incomplete pretrained encoder: {loading}')
            self.pretrained_revision = getattr(self.encoder.config, '_commit_hash', None)
            if self.pretrained_revision is None and not Path(pretrained).exists():
                cached = try_to_load_from_cache(pretrained, 'config.json')
                if isinstance(cached, str) and len(Path(cached).parent.name) == 40:
                    self.pretrained_revision = Path(cached).parent.name
        else:
            self.encoder = SegformerModel(SegformerConfig.from_dict(encoder_config))
        self.encoder_config = self.encoder.config.to_dict()
        self.frozen = freeze_encoder
        self.encoder.requires_grad_(not freeze_encoder)
        self.projections = nn.ModuleList(nn.Conv2d(c, 32, 1) for c in self.encoder.config.hidden_sizes)
        self.fuse = nn.Sequential(nn.Conv2d(128, 32, 1), nn.GroupNorm(4, 32), nn.GELU(),
                                  nn.Conv2d(32, 32, 3, padding=1), nn.GELU(), nn.Conv2d(32, 1, 1))
        self.register_buffer('mean', torch.tensor([.485, .456, .406]).view(1, 3, 1, 1))
        self.register_buffer('std', torch.tensor([.229, .224, .225]).view(1, 3, 1, 1))

    def train(self, mode=True):
        super().train(mode)
        if self.frozen:
            self.encoder.eval()
        return self

    def forward(self, x):
        normalized = (x-self.mean)/self.std
        if self.frozen:
            with torch.no_grad():
                features = self.encoder(pixel_values=normalized, output_hidden_states=True).hidden_states
        else:
            features = self.encoder(pixel_values=normalized, output_hidden_states=True).hidden_states
        size = features[0].shape[-2:]
        projected = [nn.functional.interpolate(layer(feature), size=size, mode='bilinear', align_corners=False)
                     for layer, feature in zip(self.projections, features)]
        logits = self.fuse(torch.cat(projected, dim=1))
        return nn.functional.interpolate(logits, size=x.shape[-2:], mode='bilinear', align_corners=False)


def from_checkpoint(checkpoint):
    """Construct offline from saved config; pretrained download is not needed."""
    return TransformerSegmenter(encoder_config=checkpoint['encoder_config'],
                                freeze_encoder=checkpoint.get('freeze_encoder', False))
