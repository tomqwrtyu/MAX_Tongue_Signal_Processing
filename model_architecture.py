import numpy as np
import tensorflow as tf
import config

class PositionalEmbedding(tf.keras.layers.Layer):
    def __init__(self, vocab_size = 1024, d_model = 32):
        super().__init__()
        def positional_encoding(length, depth):
            depth = depth/2

            positions = np.arange(length)[:, np.newaxis]     # (seq, 1)
            depths = np.arange(depth)[np.newaxis, :]/depth   # (1, depth)

            angle_rates = 1 / (10000**depths)         # (1, depth)
            angle_rads = positions * angle_rates      # (pos, depth)

            pos_encoding = np.concatenate(
                [np.sin(angle_rads), np.cos(angle_rads)],
                axis=-1) 

            return pos_encoding
        
        self.d_model = d_model
        self.embedding = tf.keras.layers.Embedding(vocab_size, d_model, mask_zero=True) 
        self.pos_encoding = positional_encoding(2048, d_model)

    def compute_mask(self, *args, **kwargs):
        return self.embedding.compute_mask(*args, **kwargs)

    def call(self, x):
        batch_size = tf.shape(x)[0]
        x = tf.image.extract_patches(images=x,
                                    sizes=[1, config.CHANNEL_NUMBER, 2, x.shape[-1]],
                                    strides=[1, config.CHANNEL_NUMBER, 1, x.shape[-1]],
                                    rates=[1, 1, 1, 1],
                                    padding='VALID')
        patch_dims = x.shape[-1]
        x = tf.reshape(x, [batch_size, x.shape[1] * x.shape[2], patch_dims])
        x = self.embedding(x)
        # This factor sets the relative scale of the embedding and positional_encoding.
        x *= tf.math.sqrt(tf.cast(self.d_model, tf.float16))
        pe = self.pos_encoding[np.newaxis, np.newaxis, :patch_dims, :]
        for _ in range(x.shape[1] - 1):
            pe = np.concatenate([pe, self.pos_encoding[np.newaxis, np.newaxis, :patch_dims, :]], axis=1)
        x = x + tf.cast(pe, dtype=tf.float16)
        return x
    
class EncoderLayer(tf.keras.layers.Layer):
    def __init__(self, d_model, num_heads, dff, rate=0.1):
        super(EncoderLayer, self).__init__()
        
        def point_wise_feed_forward_network(d_model, dff):
            return tf.keras.Sequential([
                tf.keras.layers.Dense(dff, activation='elu'),  # (batch_size, seq_len, dff)
                tf.keras.layers.Dense(d_model)  # (batch_size, seq_len, d_model)
            ])

        self.mha = tf.keras.layers.MultiHeadAttention(num_heads = num_heads, key_dim = d_model)
        self.ffn = point_wise_feed_forward_network(d_model, dff)

        self.layernorm1 = tf.keras.layers.LayerNormalization(epsilon=1e-6)
        self.layernorm2 = tf.keras.layers.LayerNormalization(epsilon=1e-6)

        self.dropout1 = tf.keras.layers.Dropout(rate)
        self.dropout2 = tf.keras.layers.Dropout(rate)

    def call(self, x, training = False):
        attn_output = self.mha(x, x)  # (batch_size, input_seq_len, d_model)
        attn_output = self.dropout1(attn_output, training=training)
        out1 = self.layernorm1(x + attn_output)  # (batch_size, input_seq_len, d_model)

        ffn_output = self.ffn(out1)  # (batch_size, input_seq_len, d_model)
        ffn_output = self.dropout2(ffn_output, training=training)
        out2 = self.layernorm2(out1 + ffn_output)  # (batch_size, input_seq_len, d_model)

        return out2
    
class lrs(tf.keras.optimizers.schedules.LearningRateSchedule):
    def __init__(self, d_model, warmup_steps=50):
        super().__init__()
        self.d_model = d_model
        self.d_model = tf.cast(self.d_model, tf.float32)

        self.warmup_steps = warmup_steps

    def __call__(self, step):
        arg1 = tf.math.rsqrt(step)
        arg2 = step * (self.warmup_steps ** -1.5)

        return tf.math.rsqrt(self.d_model) * tf.math.minimum(arg1, arg2)
    
    def get_config(self):
        config = {
            'd_model': self.d_model,
            'warmup_steps': self.warmup_steps,
        }
        return config
    
def ConTradiction_model(inputShape, d_model = 32, convDropRate = 0.4, encDropRate = 0.4):
    input = tf.keras.layers.Input(shape = inputShape)
    conv = tf.keras.layers.Conv2D(d_model, (1, int(config.WINDOW_SIZE * 0.5 // 3)), padding='same', activation='elu',
                            kernel_constraint=tf.keras.constraints.max_norm(0.25))(input)
    bnorm = tf.keras.layers.BatchNormalization()(conv)
    pooling = tf.keras.layers.AveragePooling2D((1, 8), padding='same')(bnorm)
    drop = tf.keras.layers.Dropout(convDropRate)(pooling)
    conv2 = tf.keras.layers.Conv2D(d_model, (1, int(config.WINDOW_SIZE * 0.5 // 6)), padding='same', activation='elu',
                            kernel_constraint=tf.keras.constraints.max_norm(0.25))(drop)
    bnorm2 = tf.keras.layers.BatchNormalization()(conv2)
    pooling2 = tf.keras.layers.AveragePooling2D((1, 4), padding='same')(bnorm2)
    drop2 = tf.keras.layers.Dropout(convDropRate)(pooling2)

    #transformer encoder
    encoder = EncoderLayer(d_model, 8, 2 * d_model, encDropRate)(drop2)
    #Classification
    flatten = tf.keras.layers.Flatten()(encoder)
    output = tf.keras.layers.Dense(config.CLASS_NUMBER, activation='softmax')(flatten)
    model = tf.keras.Model(inputs=input, outputs=output)
    model.compile(optimizer = tf.keras.optimizers.Adam(learning_rate=lrs(d_model, 50)),
                    loss = tf.keras.losses.CategoricalCrossentropy(),
                    metrics = [tf.keras.metrics.CategoricalAccuracy()])
    return model