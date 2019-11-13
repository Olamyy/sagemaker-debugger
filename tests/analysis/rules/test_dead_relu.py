# Standard Library
import argparse

# Third Party
import mxnet as mx
from mxnet import autograd, gluon
from mxnet.gluon import nn

# First Party
import smdebug.mxnet as smd
from smdebug.mxnet import Hook, SaveConfig


def parse_args():
    parser = argparse.ArgumentParser(description="Train a mxnet gluon model")
    parser.add_argument("--batch-size", type=int, default=256, help="Batch size")
    parser.add_argument(
        "--output-s3-uri",
        type=str,
        default="s3://tornasole-testing/saveall-mxnet-hook",
        help="S3 URI of the bucket where tensor data will be stored.",
    )
    parser.add_argument(
        "--smdebug_path",
        type=str,
        default=None,
        help="S3 URI of the bucket where tensor data will be stored.",
    )
    parser.add_argument("--random_seed", type=bool, default=True)
    parser.add_argument(
        "--flag",
        type=bool,
        default=True,
        help="Bool variable that indicates whether parameters will be intialized to zero",
    )
    opt = parser.parse_args()
    return opt


def create_gluon_model(flag):
    net = nn.HybridSequential()
    net.add(nn.Dense(10, activation="relu", use_bias=False))
    if flag:
        net.initialize(init=mx.initializer.Zero(), ctx=mx.cpu(0))
    else:
        net.initialize(init=mx.initializer.Xavier(), ctx=mx.cpu(0))
    return net


def train_model(batch_size, net, lr):
    softmax_cross_entropy = gluon.loss.SoftmaxCrossEntropyLoss()
    trainer = gluon.Trainer(net.collect_params(), "sgd", {"learning_rate": lr})
    for epoch in range(5):
        data = mx.nd.random.normal(shape=(100, 4, 4), ctx=mx.cpu(0))
        label = mx.nd.random.normal(shape=(100, 1), ctx=mx.cpu(0))
        with autograd.record():
            output = net(data)
            loss = softmax_cross_entropy(output, label)
        loss.backward()
        trainer.step(batch_size)


def create_hook(output_s3_uri):
    save_config = SaveConfig(save_interval=1)
    custom_collect = smd.get_collection("ReluActivation")
    custom_collect.save_config = save_config
    custom_collect.include([".*relu_output"])
    hook = Hook(
        out_dir=output_s3_uri, save_config=save_config, include_collections=["ReluActivation"]
    )
    return hook


def main():
    opt = parse_args()
    net = create_gluon_model(opt.flag)
    output_s3_uri = opt.smdebug_path if opt.smdebug_path is not None else opt.output_s3_uri
    hook = create_hook(output_s3_uri)
    hook.register_hook(net)
    train_model(64, net, 0.1, hook)


if __name__ == "__main__":
    main()