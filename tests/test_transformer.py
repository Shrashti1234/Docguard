import importlib.util
import unittest
from unittest.mock import patch
import torch


@unittest.skipUnless(importlib.util.find_spec('transformers'), 'Optional Transformer dependencies not installed')
class TransformerChecks(unittest.TestCase):
    def model(self, frozen):
        from transformers import SegformerConfig
        from docguard.transformer import TransformerSegmenter
        config = SegformerConfig(hidden_sizes=[8, 16, 32, 64], depths=[1, 1, 1, 1],
                                 num_attention_heads=[1, 2, 4, 8], decoder_hidden_size=32)
        return TransformerSegmenter(encoder_config=config.to_dict(), freeze_encoder=frozen)

    def test_frozen_encoder_and_output_alignment(self):
        torch.set_num_threads(2)
        model = self.model(True).train()
        self.assertFalse(model.encoder.training)
        x = torch.rand(2, 3, 65, 67)
        out = model(x)
        self.assertEqual(tuple(out.shape), (2, 1, 65, 67))
        out.mean().backward()
        self.assertTrue(all(p.grad is None for p in model.encoder.parameters()))
        self.assertTrue(any(p.grad is not None for p in model.fuse.parameters()))

    def test_finetuning_and_offline_checkpoint_restore(self):
        from docguard.transformer import from_checkpoint
        model = self.model(False)
        x = torch.rand(1, 3, 64, 64)
        model(x).mean().backward()
        self.assertTrue(any(p.grad is not None and torch.isfinite(p.grad).all() for p in model.encoder.parameters()))
        checkpoint = dict(encoder_config=model.encoder_config, state_dict=model.state_dict())
        with patch('docguard.transformer.SegformerModel.from_pretrained', side_effect=AssertionError('Offline restore tried network')):
            restored = from_checkpoint(checkpoint)
            restored.load_state_dict(checkpoint['state_dict'])
        model.eval()
        restored.eval()
        with torch.no_grad():
            self.assertTrue(torch.allclose(model(x), restored(x), atol=1e-6))


if __name__ == '__main__':
    unittest.main()
