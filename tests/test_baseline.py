import unittest
import torch
from docguard.baseline import SmallUNet, counts_to_metrics, segmentation_loss, evaluate


class BaselineChecks(unittest.TestCase):
    def test_metric_counts(self):
        result = counts_to_metrics(3, 1, 2)
        self.assertAlmostEqual(result['precision'], .75)
        self.assertAlmostEqual(result['recall'], .6)
        self.assertAlmostEqual(result['f1'], 2/3)
        self.assertAlmostEqual(result['iou'], .5)
        self.assertEqual(counts_to_metrics(0, 0, 0)['f1'], 0)

    def test_odd_dimensions_and_negative_batch_gradients(self):
        torch.set_num_threads(2)
        model = SmallUNet()
        x = torch.randn(2, 3, 33, 29)
        logits = model(x)
        self.assertEqual(tuple(logits.shape), (2, 1, 33, 29))
        for positive in (False, True):
            target = torch.zeros_like(logits)
            if positive:
                target[:, :, 10:15, 8:12] = 1
            model.zero_grad()
            loss = segmentation_loss(model(x), target, torch.tensor(20.0))
            loss.backward()
            self.assertTrue(torch.isfinite(loss))
            self.assertTrue(all(torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None))

    def test_evaluation_counts_false_alarms_on_negatives(self):
        # First image is a true positive; second is an authentic false alarm.
        logits = torch.tensor([[[[10., -10.], [-10., -10.]]],
                               [[[10., -10.], [-10., -10.]]]])
        truth = torch.zeros_like(logits)
        truth[0, 0, 0, 0] = 1
        class Fixed(torch.nn.Module):
            def forward(self, x):
                return logits
        loader = [(torch.zeros(2, 3, 2, 2), truth, torch.arange(2))]
        result = evaluate(Fixed(), loader, torch.device('cpu'), [.5])[0][.5]
        self.assertEqual((result['tp'], result['fp'], result['fn']), (1, 1, 0))
        self.assertEqual(result['authentic_documents'], 1)
        self.assertEqual(result['authentic_false_positive_rate'], 1)


if __name__ == '__main__':
    unittest.main()
