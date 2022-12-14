# -*- coding: utf-8 -*-
"""gen_andreas_images_wgan

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/127n6tPV0eYrQwHmnvn7eD-m62nhNBfRJ

# WGAN-GP overriding `Model.train_step`

**Author:** [A_K_Nain](https://twitter.com/A_K_Nain)<br>
**Date created:** 2020/05/9<br>
**Last modified:** 2020/05/9<br>
**Description:** Implementation of Wasserstein GAN with Gradient Penalty.

## Wasserstein GAN (WGAN) with Gradient Penalty (GP)

The original [Wasserstein GAN](https://arxiv.org/abs/1701.07875) leverages the
Wasserstein distance to produce a value function that has better theoretical
properties than the value function used in the original GAN paper. WGAN requires
that the discriminator (aka the critic) lie within the space of 1-Lipschitz
functions. The authors proposed the idea of weight clipping to achieve this
constraint. Though weight clipping works, it can be a problematic way to enforce
1-Lipschitz constraint and can cause undesirable behavior, e.g. a very deep WGAN
discriminator (critic) often fails to converge.

The [WGAN-GP](https://arxiv.org/pdf/1704.00028.pdf) method proposes an
alternative to weight clipping to ensure smooth training. Instead of clipping
the weights, the authors proposed a "gradient penalty" by adding a loss term
that keeps the L2 norm of the discriminator gradients close to 1.

## Setup
"""



import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import scipy.io
import os
os.environ['CUDA_VISIBLE_DEVICES']= '0'
print(tf.test.is_gpu_available())
print(tf.test.gpu_device_name())
"""## Prepare the Fashion-MNIST data

To demonstrate how to train WGAN-GP, we will be using the
[Fashion-MNIST](https://github.com/zalandoresearch/fashion-mnist) dataset. Each
sample in this dataset is a 28x28 grayscale image associated with a label from
10 classes (e.g. trouser, pullover, sneaker, etc.)
"""

IMG_SHAPE = (40, 40, 1)
BATCH_SIZE = 10

# Size of the noise vector
noise_dim = 128
"""
fashion_mnist = keras.datasets.fashion_mnist
(train_images, train_labels), (test_images, test_labels) = fashion_mnist.load_data()
print(np.shape(train_images))
print(np.shape(train_labels))

print(f"Number of examples: {len(train_images)}")
print(f"Shape of the images in the dataset: {train_images.shape[1:]}")

# Reshape each sample to (28, 28, 1) and normalize the pixel values in the [-1, 1] range
train_images = train_images.reshape(train_images.shape[0], *IMG_SHAPE).astype("float32")
train_images = (train_images - 127.5) / 127.5
"""

matlab_matrix=scipy.io.loadmat('fluence_train_data.mat');

ground_truths  = matlab_matrix['p0_volumes']
simulated_image_examples = matlab_matrix['mua_volumes']

train_images = np.copy(simulated_image_examples)
train_images = np.squeeze(train_images)
train_images = np.expand_dims(train_images,axis=3)

train_images = tf.cast(train_images,dtype=tf.float32)

ground_truths = np.copy(ground_truths)
ground_truths = np.squeeze(ground_truths)
ground_truths = np.expand_dims(ground_truths,axis=3)
ground_truths = tf.cast(ground_truths,dtype=tf.float32)


train_images = train_images[600:999,:,:,:]
ground_truths_train_data = ground_truths[600:999,:,:,:]


def conv_block(
    x,
    filters,
    activation,
    kernel_size=(3, 3),
    strides=(1, 1),
    padding="same",
    use_bias=True,
    use_bn=False,
    use_dropout=False,
    drop_value=0.5,
):
    x = layers.Conv2D(
        filters, kernel_size, strides=strides, padding=padding, use_bias=use_bias
    )(x)
    if use_bn:
        x = layers.BatchNormalization()(x)
    x = activation(x)
    if use_dropout:
        x = layers.Dropout(drop_value)(x)
    return x


def get_discriminator_model():
    img_input = layers.Input(shape=IMG_SHAPE)
    """
    # Zero pad the input to make the input images size to (32, 32, 1).
    x = layers.ZeroPadding2D((2, 2))(img_input)
    sub_factor = tf.ones_like(x)
    sub_factor = tf.scalar_mul(0.5,sub_factor)
    x = layers.subtract([x,sub_factor])
    """
    #sub_factor = tf.ones_like(img_input)
    #sub_factor = tf.scalar_mul(-np.mean(train_images),sub_factor)
    #print(np.shape(sub_factor))
    #x = layers.Add()([img_input,sub_factor])
    
    x = layers.ZeroPadding2D((2, 2))(img_input)#x
    
    #print("subfactor shape:")
    #print(np.shape(sub_factor))
    
    #img_input = layers.subtract([img_input,sub_factor])
    x = conv_block(
        x,
        64,
        kernel_size=(3, 3),
        strides=(2, 2),
        use_bn=False,
        use_bias=True,
        activation=layers.LeakyReLU(0.2),
        use_dropout=False,
        drop_value=0.3,
    )
    x = conv_block(
        x,
        128,
        kernel_size=(3, 3),
        strides=(2, 2),
        use_bn=False,
        activation=layers.LeakyReLU(0.2),
        use_bias=True,
        use_dropout=True,
        drop_value=0.3,
    )
    #x = conv_block(
    #    x,
    #    256,
    #    kernel_size=(3, 3),
    #    strides=(2, 2),
    #    use_bn=False,
    #    activation=layers.LeakyReLU(0.2),
    #    use_bias=True,
    #    use_dropout=True,
    #    drop_value=0.3,
    #)
    #x = conv_block(
    #    x,
    #    512,
    #    kernel_size=(5, 5),
    #    strides=(2, 2),
    #    use_bn=False,
    #    activation=layers.LeakyReLU(0.2),
    #    use_bias=True,
    #    use_dropout=False,
    #    drop_value=0.3,
    #)

    x = layers.Flatten()(x)
    x = layers.Dropout(0.2)(x)
    x = layers.Dense(1)(x)

    d_model = keras.models.Model(img_input, x, name="discriminator")
    return d_model


d_model = get_discriminator_model()
d_model.summary()

"""## Create the generator

"""

def upsample_block(
    x,
    filters,
    activation,
    kernel_size=(3, 3),
    strides=(1, 1),
    up_size=(2, 2),
    padding="same",
    use_bn=False,
    use_bias=True,
    use_dropout=False,
    drop_value=0.3,
):
    x = layers.UpSampling2D(up_size)(x)
    x = layers.Conv2D(
        filters, kernel_size, strides=strides, padding=padding, use_bias=use_bias
    )(x)

    if use_bn:
        x = layers.BatchNormalization()(x)

    if activation:
        x = activation(x)
    if use_dropout:
        x = layers.Dropout(drop_value)(x)
    return x


def get_generator_model():
    noise = layers.Input(shape=(noise_dim,))
    x = layers.Dense(5 * 5 * 256, use_bias=False)(noise)
    x = layers.BatchNormalization()(x)
    x = layers.LeakyReLU(0.2)(x)

    x = layers.Reshape((5, 5, 256))(x)
    x = upsample_block(
        x,
        128,
        layers.LeakyReLU(0.2),
        strides=(1, 1),
        use_bias=False,
        use_bn=True,
        padding="same",
        use_dropout=False,
    )
    x = upsample_block(
        x,
        64,
        layers.LeakyReLU(0.2),
        strides=(1, 1),
        use_bias=False,
        use_bn=True,
        padding="same",
        use_dropout=False,
    )
#, layers.LeakyReLU(0.2)
    gen_tissue_model = upsample_block(
        x, 1, layers.Activation("sigmoid"), strides=(1, 1), use_bias=False, use_bn=True
    )
    
    g_model = keras.models.Model(noise, gen_tissue_model, name="generator")
    return g_model


g_model = get_generator_model()
g_model.summary()

def get_generator_end_model():
    tissue_model_input =layers.Input(shape=IMG_SHAPE)
    conv1 = layers.Conv2D(64, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(tissue_model_input)
    conv1 = layers.Conv2D(64, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv1)
    pool1 = layers.MaxPooling2D(pool_size=(2, 2))(conv1)
    conv2 = layers.Conv2D(128, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(pool1)
    conv2 = layers.Conv2D(128, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv2)
    pool2 = layers.MaxPooling2D(pool_size=(2, 2))(conv2)
    conv3 = layers.Conv2D(256, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(pool2)
    conv3 = layers.Conv2D(256, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv3)
    up8 = layers.Conv2D(128, 2, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(layers.UpSampling2D(size = (2,2))(conv3))
    
    conv8 = layers.Conv2D(128, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(up8)
    conv8 = layers.Conv2D(128, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv8)

    up9 = layers.Conv2D(64, 2, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(layers.UpSampling2D(size = (2,2))(conv8))
    
    conv9 = layers.Conv2D(64, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(up9)
    conv9 = layers.Conv2D(64, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv9)
    conv9 = layers.Conv2D(2, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv9)
    conv10 = layers.Conv2D(1, 1, activation = 'relu')(conv9)

       
    g_model_end = keras.models.Model(tissue_model_input, conv10, name="g_model_end")
    return g_model_end


g_model_end = get_generator_end_model()
g_model_end.summary()

"""## Create the WGAN-GP model

Now that we have defined our generator and discriminator, it's time to implement
the WGAN-GP model. We will also override the `train_step` for training.
"""

class WGAN(keras.Model):
    def __init__(
        self,
        discriminator,
        generator,
        generator_end,
        latent_dim,
        discriminator_extra_steps=3,
        gp_weight=10.0,
    ):
        super(WGAN, self).__init__()
        self.discriminator = discriminator
        self.generator = generator
        self.generator_end = generator_end
        self.latent_dim = latent_dim
        self.d_steps = discriminator_extra_steps
        self.gp_weight = gp_weight

    def compile(self, d_optimizer, g_optimizer, f_optimizer, d_loss_fn, g_loss_fn, f_loss_fn):
        super(WGAN, self).compile()
        self.d_optimizer = d_optimizer
        self.g_optimizer = g_optimizer
        self.f_optimizer = f_optimizer
        self.d_loss_fn = d_loss_fn
        self.g_loss_fn = g_loss_fn
        self.f_loss_fn = f_loss_fn

    def gradient_penalty(self, batch_size, real_images, fake_images):
        """ Calculates the gradient penalty.

        This loss is calculated on an interpolated image
        and added to the discriminator loss.
        """
        # Get the interpolated image
        alpha = tf.random.normal([batch_size, 1, 1, 1], 0.0, 1.0)
        diff = fake_images - real_images
        interpolated = real_images + alpha * diff

        with tf.GradientTape() as gp_tape:
            gp_tape.watch(interpolated)
            # 1. Get the discriminator output for this interpolated image.
            pred = self.discriminator(interpolated, training=True)

        # 2. Calculate the gradients w.r.t to this interpolated image.
        grads = gp_tape.gradient(pred, [interpolated])[0]
        # 3. Calculate the norm of the gradients.
        norm = tf.sqrt(tf.reduce_sum(tf.square(grads), axis=[1, 2, 3]))
        gp = tf.reduce_mean((norm - 1.0) ** 2)
        return gp

    def train_step(self, real_images):
        if isinstance(real_images, tuple):
            real_images = real_images[0]

        # Get the batch size
        batch_size = tf.shape(real_images)[0]

        # For each batch, we are going to perform the
        # following steps as laid out in the original paper:
        # 1. Train the generator and get the generator loss
        # 2. Train the discriminator and get the discriminator loss
        # 3. Calculate the gradient penalty
        # 4. Multiply this gradient penalty with a constant weight factor
        # 5. Add the gradient penalty to the discriminator loss
        # 6. Return the generator and discriminator losses as a loss dictionary

        # Train the discriminator first. The original paper recommends training
        # the discriminator for `x` more steps (typically 5) as compared to
        # one step of the generator. Here we will train it for 3 extra steps
        # as compared to 5 to reduce the training time.
        for i in range(self.d_steps):
            # Get the latent vector
            random_latent_vectors = tf.random.normal(
                shape=(batch_size, self.latent_dim)
            )
            with tf.GradientTape() as tape:
                # Generate fake images from the latent vector
                fake_tissue = self.generator(random_latent_vectors, training=True)
                fake_images = self.generator_end(fake_tissue, training=True)

                # Get the logits for the fake images
                fake_logits = self.discriminator(fake_images, training=True)
                # Get the logits for the real images
                real_logits = self.discriminator(real_images, training=True)

                # Calculate the discriminator loss using the fake and real image logits
                d_cost = self.d_loss_fn(real_img=real_logits, fake_img=fake_logits)
                # Calculate the gradient penalty
                gp = self.gradient_penalty(batch_size, real_images, fake_images)
                # Add the gradient penalty to the original discriminator loss
                d_loss = d_cost + gp * self.gp_weight

            # Get the gradients w.r.t the discriminator loss
            d_gradient = tape.gradient(d_loss, self.discriminator.trainable_variables)
            # Update the weights of the discriminator using the discriminator optimizer
            self.d_optimizer.apply_gradients(
                zip(d_gradient, self.discriminator.trainable_variables)
            )

        # Train the generator
        # Get the latent vector
        random_latent_vectors = tf.random.normal(shape=(batch_size, self.latent_dim))
        with tf.GradientTape() as tape:
            # Generate fake images using the generator
            generated_tissues = self.generator(random_latent_vectors, training=True)
            generated_images = self.generator_end(generated_tissues, training=True)
            
            # Get the discriminator logits for fake images
            gen_img_logits = self.discriminator(generated_images, training=True)
            # Calculate the generator loss
            g_loss = self.g_loss_fn(gen_img_logits)

        # Get the gradients w.r.t the generator loss
        gen_gradient = tape.gradient(g_loss, self.generator.trainable_variables)
        # Update the weights of the generator using the generator optimizer
        self.g_optimizer.apply_gradients(
            zip(gen_gradient, self.generator.trainable_variables)
        )
        return {"d_loss": d_loss, "g_loss": g_loss}

"""## Create a Keras callback that periodically saves generated images"""

class GANMonitor(keras.callbacks.Callback):
    def __init__(self, num_img=6, latent_dim=128):
        self.num_img = num_img
        self.latent_dim = latent_dim
    def on_epoch_end(self, epoch, logs=None):
        random_latent_vectors = tf.random.normal(shape=(self.num_img, self.latent_dim))
        generated_tissues = self.model.generator(random_latent_vectors)
        generated_images = self.model.generator_end(generated_tissues)
        #generated_images = (generated_images * 127.5) + 127.5
        #if epoch % 100 == 1:
        img = generated_images.numpy()
        tiss = generated_tissues.numpy()
        filename = "img_%s.mat" % epoch
        scipy.io.savemat(filename, {'img':img})
        filename = "tiss_%s.mat" % epoch
        scipy.io.savemat(filename, {'tiss':tiss})        #fluence_images = self.model.generator_end(vali_inputs)
        #fluence = fluence_images.numpy()
        
        #filename = "fluence_%s.mat" % epoch
        #scipy.io.savemat(filename, {'fluence':fluence})

# Instantiate the optimizer for both networks
# (learning_rate=0.0002, beta_1=0.5 are recommended)
generator_optimizer = keras.optimizers.Adam(
    learning_rate=0.0002, beta_1=0.5, beta_2=0.9
)
discriminator_optimizer = keras.optimizers.Adam(
    learning_rate=0.0002, beta_1=0.5, beta_2=0.9
)

# Define the loss functions for the discriminator,
# which should be (fake_loss - real_loss).
# We will add the gradient penalty later to this loss function.
def discriminator_loss(real_img, fake_img):
    real_loss = tf.reduce_mean(real_img)
    fake_loss = tf.reduce_mean(fake_img)
    return fake_loss - real_loss


# Define the loss functions for the generator.
def generator_loss(fake_img):
    return -tf.reduce_mean(fake_img)

def fluence_loss(gen_fluence_out,gen_fluence_truth):
    return tf.norm(tf.square(gen_fluence_out - gen_fluence_truth))



# Set the number of epochs for trainining.
epochs = 5000

# Instantiate the customer `GANMonitor` Keras callback.
cbk = GANMonitor()

# Instantiate the WGAN model.
wgan = WGAN(
    discriminator=d_model,
    generator=g_model,
    generator_end=g_model_end,
    latent_dim=noise_dim,
    discriminator_extra_steps=3,
)

# Compile the WGAN model.
wgan.compile(
    d_optimizer=discriminator_optimizer,
    g_optimizer=generator_optimizer,
    f_optimizer = discriminator_optimizer,
    g_loss_fn=generator_loss,
    d_loss_fn=discriminator_loss,
    f_loss_fn = fluence_loss
)

checkpoint_filepath = "model_checkpoints_full_gan/cyclegan_checkpoints.{epoch:03d}"
model_checkpoint_callback = keras.callbacks.ModelCheckpoint(
    filepath=checkpoint_filepath
)


# Load the checkpoints
weight_file = "./model_checkpoints/checkpoints.080"#16 #22?
#weight_file = "./cyclegan_checkpoints.007"

wgan.load_weights(weight_file).expect_partial()
print("Weights loaded successfully")

# Start training the model.
history_callback=wgan.fit(train_images, batch_size=BATCH_SIZE, epochs=epochs, callbacks=[cbk,model_checkpoint_callback])



d_loss_hist = history_callback.history["d_loss"]
g_loss_hist = history_callback.history["g_loss"]
"""Display the last generated images:

"""
scipy.io.savemat('d_loss_hist.mat', {'d_loss_hist':d_loss_hist})

scipy.io.savemat('g_loss_hist.mat', {'g_loss_hist':g_loss_hist})

