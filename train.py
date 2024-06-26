from pytorch_lightning import Trainer
from pytorch_lightning.callbacks import ModelCheckpoint
from pytorch_lightning.loggers import TensorBoardLogger

from config import get_opts
from data_modules import VideosDataModule
from SC_Depth import SC_Depth
from PC_Depth import PC_Depth

import warnings


if __name__ == '__main__':
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    hparams = get_opts()

    # pl model
    if hparams.model_version == 'SC-Depth':
        system = SC_Depth(hparams)
    elif hparams.model_version == 'PC-Depth':
        system = PC_Depth(hparams)

    # pl data module
    dm = VideosDataModule(hparams)

    # pl logger
    logger = TensorBoardLogger(
        save_dir="log",
        name=hparams.exp_name
    )

    # save checkpoints
    ckpt_dir = 'log/{}/version_{:d}'.format(
        hparams.exp_name, logger.version)
    checkpoint_callback = ModelCheckpoint(dirpath=ckpt_dir,
                                          filename='{epoch}-{val_loss:.4f}',
                                          monitor='val_loss',
                                          mode='min',
                                          save_last=True,
                                          save_weights_only=True,
                                          save_top_k=3)

    # restore from previous checkpoints
    if hparams.ckpt_path is not None:
        print('load pre-trained model from {}'.format(hparams.ckpt_path))
        system = system.load_from_checkpoint(
            hparams.ckpt_path, strict=False, hparams=hparams)

    # set up trainer
    trainer = Trainer(
        accelerator='gpu',
        max_epochs=hparams.num_epochs,
        # limit_train_batches=hparams.epoch_size,
        limit_val_batches=400,
        num_sanity_val_steps=0,
        callbacks=[checkpoint_callback],
        logger=logger,
        benchmark=True
    )

    trainer.fit(system, dm)
