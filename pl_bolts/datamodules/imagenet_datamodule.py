import os

from torch.utils.data import DataLoader
from torchvision import transforms as transform_lib

from pytorch_lightning import LightningDataModule
from pl_bolts.datamodules.imagenet_dataset import UnlabeledImagenet
from pl_bolts.transforms.dataset_normalizations import imagenet_normalization


class ImagenetDataModule(LightningDataModule):

    name = 'imagenet'

    def __init__(
            self,
            data_dir: str,
            meta_dir: str = None,
            num_imgs_per_val_class: int = 50,
            image_size: int = 224,
            num_workers: int = 16,
            *args,
            **kwargs,
    ):
        """
        Imagenet train, val and test dataloaders.

        The train set is the imagenet train.

        The val set is taken from the train set with `num_imgs_per_val_class` images per class.
        For example if `num_imgs_per_val_class=2` then there will be 2,000 images in the validation set.

        The test set is the official imagenet validation set.

         Example::

            from pl_bolts.datamodules import ImagenetDataModule

            datamodule = ImagenetDataModule(IMAGENET_PATH)

        Args:

            data_dir: path to the imagenet dataset file
            meta_dir: path to meta.bin file
            num_imgs_per_val_class: how many images per class for the validation set
            image_size: final image size
            num_workers: how many data workers
        """
        super().__init__(*args, **kwargs)
        self.image_size = image_size
        self.dims = (3, self.image_size, self.image_size)
        self.data_dir = data_dir
        self.num_workers = num_workers
        self.meta_dir = meta_dir
        self.num_imgs_per_val_class = num_imgs_per_val_class

    @property
    def num_classes(self):
        """
        Return:

            1000

        """
        return 1000

    def _verify_splits(self, data_dir, split):
        dirs = os.listdir(data_dir)

        if split not in dirs:
            raise FileNotFoundError(f'a {split} Imagenet split was not found in {data_dir},'
                                    f' make sure the folder contains a subfolder named {split}')

    def prepare_data(self):
        """
        This method already assumes you have imagenet2012 downloaded.
        It validates the data using the meta.bin.

        .. warning:: Please download imagenet on your own first.
        """
        self._verify_splits(self.data_dir, 'train')
        self._verify_splits(self.data_dir, 'val')

        for split in ['train', 'val']:
            files = os.listdir(os.path.join(self.data_dir, split))
            if 'meta.bin' not in files:
                raise FileNotFoundError("""
                no meta.bin present. Imagenet is no longer automatically downloaded by PyTorch.
                To get imagenet:
                1. download yourself from http://www.image-net.org/challenges/LSVRC/2012/downloads
                2. download the devkit (ILSVRC2012_devkit_t12.tar.gz)
                3. generate the meta.bin file using the devkit
                4. copy the meta.bin file into both train and val split folders

                To generate the meta.bin do the following:

                from pl_bolts.datamodules.imagenet_dataset import UnlabeledImagenet
                path = '/path/to/folder/with/ILSVRC2012_devkit_t12.tar.gz/'
                UnlabeledImagenet.generate_meta_bins(path)
                """)

    def train_dataloader(self, batch_size):
        """
        Uses the train split of imagenet2012 and puts away a portion of it for the validation split

        Args:
            batch_size: the batch size
            transforms: the transforms
        """
        transforms = self.train_transform() if self.train_transforms is None else self.train_transforms

        dataset = UnlabeledImagenet(self.data_dir,
                                    num_imgs_per_class=-1,
                                    meta_dir=self.meta_dir,
                                    split='train',
                                    transform=transforms)
        loader = DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=self.num_workers,
            drop_last=True,
            pin_memory=True
        )
        return loader

    def val_dataloader(self, batch_size, transforms=None):
        """
        Uses the part of the train split of imagenet2012  that was not used for training via `num_imgs_per_val_class`

        Args:
            batch_size: the batch size
            transforms: the transforms
        """
        transforms = self.train_transform() if self.val_transforms is None else self.val_transforms

        dataset = UnlabeledImagenet(self.data_dir,
                                    num_imgs_per_class_val_split=self.num_imgs_per_val_class,
                                    meta_dir=self.meta_dir,
                                    split='val',
                                    transform=transforms)
        loader = DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            pin_memory=True
        )
        return loader

    def test_dataloader(self, batch_size, num_images_per_class=-1, transforms=None):
        """
        Uses the validation split of imagenet2012 for testing

        Args:
            batch_size: the batch size
            num_images_per_class: how many images per class to test on
            transforms: the transforms
        """
        transforms = self.val_transform() if self.test_transforms is None else self.test_transforms

        dataset = UnlabeledImagenet(self.data_dir,
                                    num_imgs_per_class=num_images_per_class,
                                    meta_dir=self.meta_dir,
                                    split='test',
                                    transform=transforms)
        loader = DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            drop_last=True,
            pin_memory=True
        )
        return loader

    def train_transform(self):
        """
        The standard imagenet transforms

        .. code-block:: python

            transform_lib.Compose([
                transform_lib.RandomResizedCrop(self.image_size),
                transform_lib.RandomHorizontalFlip(),
                transform_lib.ToTensor(),
                transform_lib.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                ),
            ])

        """
        preprocessing = transform_lib.Compose([
            transform_lib.RandomResizedCrop(self.image_size),
            transform_lib.RandomHorizontalFlip(),
            transform_lib.ToTensor(),
            imagenet_normalization(),
        ])

        return preprocessing

    def val_transform(self):
        """
        The standard imagenet transforms for validation

        .. code-block:: python

            transform_lib.Compose([
                transform_lib.Resize(self.image_size + 32),
                transform_lib.CenterCrop(self.image_size),
                transform_lib.ToTensor(),
                transform_lib.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                ),
            ])

        """

        preprocessing = transform_lib.Compose([
            transform_lib.Resize(self.image_size + 32),
            transform_lib.CenterCrop(self.image_size),
            transform_lib.ToTensor(),
            imagenet_normalization(),
        ])
        return preprocessing
