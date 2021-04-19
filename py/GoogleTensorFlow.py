import logging
import os
import tensorflow as tf
import keras
from keras.applications.vgg16 import VGG16, decode_predictions, preprocess_input
from keras.applications.resnet50 import preprocess_input, decode_predictions
from keras.models import load_model
from keras.models import Sequential, Model
from keras.layers import Conv2D, MaxPooling2D
from keras.layers import Dense, Dropout, Flatten, GlobalAveragePooling2D, Input
from keras.optimizers import SGD, Adam
from keras.preprocessing import image
from keras.preprocessing.image import ImageDataGenerator
from keras.utils import np_utils
import keras.callbacks
import numpy as np
import json
import random, math
from PIL import Image

logger = logging.getLogger(__name__)

class GoogleTensorFlow(object):
    def __init__(self, default_dir, file_name='base', image_size=224):
        logger.info(tf.test.gpu_device_name())

        # GPUのメモリ制限
        physical_devices = tf.config.experimental.list_physical_devices('GPU')
        if len(physical_devices) > 0:
            for k in range(len(physical_devices)):
                tf.config.experimental.set_memory_growth(physical_devices[k], True)
                print('memory growth:', tf.config.experimental.get_memory_growth(physical_devices[k]))
        else:
            print("Not enough GPU hardware devices available")
        self.DEFAULT_DIR = default_dir
        self.IMAGE_SIZE = image_size # VGG16の学習済みモデルの入力サイズは224x224 imagenet は 48以上
        self.IMAGE_SIZES = (self.IMAGE_SIZE, self.IMAGE_SIZE)
        # 学習条件
        self.BATCH_SIZE = 64 # default 一度に読み込むファイル数　学習効率には関係ないか？
        self.EPOCH_SIZE = 50 # default 学習の繰り返し数 学習率をみて、最終的に決定
        # Compile条件
        #self.LEARNING_RATE = 0.01 # 勾配、学習効率 SGD
        self.LEARNING_RATE = 0.001 # 勾配、学習効率 Adam
        self.EPSILON = 1e-8 # 1e-7 Adam
        self.DECAY = 1e-4 # 1e-3 から 1e-6
        self.MOMENTUM = 0.9 # SGD Adam bata_1
        # モデルおよびカテゴリーの保存
        file_name = "base" if file_name == "" else file_name
        self.hdf5_file = os.path.join(default_dir, str(image_size) + '_' + file_name + '.hdf5')
        self.class_file = os.path.join(default_dir, str(image_size) + '_' + file_name +  '.json')         

    # ディレクトリからトレーニングデータの作成
    def createTrainData(self, modelDir, categories):
        try:
            sample_dir = os.path.join(self.DEFAULT_DIR, modelDir)
            categories += [name for name in os.listdir(sample_dir) if name != ".DS_Store"]
            # 画像読み込み
            train_data = [] 
            for i, sdir in enumerate(categories): 
                logger.info(f"sdir: {sdir}")
                files = [name for name in os.listdir(os.path.join(sample_dir, sdir)) if name != ".DS_Store"]
                for f in files:
                    filename = os.path.join(sample_dir, sdir, f)
                    logger.debug(filename)
                    if os.path.isfile(filename) == False:
                        logger.error(f"file none: {filename}")
                        continue
                    data = self.createDataFromImage(filename)
                    train_data.append([data,i])

            # シャッフル
            random.shuffle(train_data)
            X, Y = [],[]
            for data in train_data: 
                X.append(data[0])
                Y.append(data[1])

            test_idx = math.floor(len(X) * 0.8)
            xy = (np.array(X[0:test_idx]), np.array(X[test_idx:]), 
                np.array(Y[0:test_idx]), np.array(Y[test_idx:]))

            return xy

        except Exception as e:
            logger.error('trainData not create')
            logger.error(e)


    # 画像ファイルからデータを作成
    def createDataFromImage(self, file):
        try:
            with Image.open(file) as img:
                rgb = img.convert("RGB")
            rgb = rgb.resize(self.IMAGE_SIZES)
            data = np.array(rgb)
            return data
        except Exception as e:
            logger.error('image not load')
            logger.error(e)
            return None

    # Model の作成(素数用とりあえず)
    def createModelFromShapeSosu(self, categorys):
        model = Sequential()
        # 入力: サイズが指定x指定で3チャンネル（RGB）をもつ画像 -> (指定, 指定, 3) のテンソル
        # それぞれのlayerで3x3の畳み込み処理を適用している
        model.add(Conv2D(32, (3, 3), activation='relu', input_shape=(1, 1, 1)))
        model.add(Conv2D(32, (3, 3), activation='relu'))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Dropout(0.25))

        model.add(Conv2D(64, (3, 3), activation='relu'))
        model.add(Conv2D(64, (3, 3), activation='relu'))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Dropout(0.25))

        # 結合
        model.add(Flatten())
        model.add(Dense(256, activation='relu'))
        model.add(Dropout(0.5))

        # 最終的にcategorys分だけ分類する
        model.add(Dense(categorys, activation='softmax'))

        # SGD
        #sgd = SGD(lr=self.LEARNING_RATE, decay=self.DECAY, momentum=self.MOMENTUM, nesterov=True)
        #model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])
        #Adam
        adam = Adam(learning_rate=self.LEARNING_RATE, beta_1=self.MOMENTUM, beta_2=0.999, epsilon=self.EPSILON, decay=self.DECAY, amsgrad=False, name='Adam')
        model.compile(loss='categorical_crossentropy', optimizer=adam, metrics=['accuracy'])
        return model


    # Model の作成
    def createModelFromShape(self, categorys):
        model = Sequential()
        # 入力: サイズが指定x指定で3チャンネル（RGB）をもつ画像 -> (指定, 指定, 3) のテンソル
        # それぞれのlayerで3x3の畳み込み処理を適用している
        model.add(Conv2D(32, (3, 3), activation='relu', input_shape=(self.IMAGE_SIZE, self.IMAGE_SIZE, 3)))
        model.add(Conv2D(32, (3, 3), activation='relu'))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Dropout(0.25))

        model.add(Conv2D(64, (3, 3), activation='relu'))
        model.add(Conv2D(64, (3, 3), activation='relu'))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Dropout(0.25))

        # 結合
        model.add(Flatten())
        model.add(Dense(256, activation='relu'))
        model.add(Dropout(0.5))

        # 最終的にcategorys分だけ分類する
        model.add(Dense(categorys, activation='softmax'))

        # SGD
        #sgd = SGD(lr=self.LEARNING_RATE, decay=self.DECAY, momentum=self.MOMENTUM, nesterov=True)
        #model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])
        #Adam
        adam = Adam(learning_rate=self.LEARNING_RATE, beta_1=self.MOMENTUM, beta_2=0.999, epsilon=self.EPSILON, decay=self.DECAY, amsgrad=False, name='Adam')
        model.compile(loss='categorical_crossentropy', optimizer=adam, metrics=['accuracy'])
        return model


    # VGGの転移学習用のモデル追加(1個でやってみよう)
    def addModelFromShapeSigmoid(self):
        # 元となるモデルの読み込み
        base_model=VGG16(weights='imagenet', include_top=False,
                 input_tensor=Input(shape=(self.IMAGE_SIZE, self.IMAGE_SIZE, 3)))

        # 自分で作成した分類を追加
        x = base_model.output
        x = GlobalAveragePooling2D()(x)
        x = Dense(1024, activation='relu')(x)
        prediction = Dense(1, activation='sigmoid')(x)
        model = Model(inputs=base_model.input, outputs=prediction)

        # 元のは学習しない fix weights before VGG16 14layers
        for layer in base_model.layers[:15]:
            layer.trainable=False

        # SGD
        # sgd = SGD(lr=self.LEARNING_RATE, decay=self.DECAY, momentum=self.MOMENTUM, nesterov=True)
        # model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])
        #Adam
        adam = Adam(learning_rate=self.LEARNING_RATE, beta_1=self.MOMENTUM, beta_2=0.999, epsilon=self.EPSILON, decay=self.DECAY, amsgrad=False, name='Adam')
        model.compile(loss='categorical_crossentropy', optimizer=adam, metrics=['accuracy'])
        return model


    # VGGの転移学習用のモデル追加
    def addModelFromShape(self, categorys):
        # 元となるモデルの読み込み
        base_model=VGG16(weights='imagenet', include_top=False,
                 input_tensor=Input(shape=(self.IMAGE_SIZE, self.IMAGE_SIZE, 3)))

        # 自分で作成した分類を追加
        x = base_model.output
        x = GlobalAveragePooling2D()(x)
        x = Dense(1024, activation='relu')(x)
        prediction = Dense(categorys, activation='softmax')(x)
        model = Model(inputs=base_model.input, outputs=prediction)

        # 元のは学習しない fix weights before VGG16 14layers
        for layer in base_model.layers[:15]:
            layer.trainable=False

        # SGD
        # sgd = SGD(lr=self.LEARNING_RATE, decay=self.DECAY, momentum=self.MOMENTUM, nesterov=True)
        # model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])
        #Adam
        adam = Adam(learning_rate=self.LEARNING_RATE, beta_1=self.MOMENTUM, beta_2=0.999, epsilon=self.EPSILON, decay=self.DECAY, amsgrad=False, name='Adam')
        model.compile(loss='categorical_crossentropy', optimizer=adam, metrics=['accuracy'])
        return model


    def saveModelGenerator(self, modelDir, validDir, batch_size=0, epoch_size=0, mode_add=False, mode_bin=False):
        '''
        # Generatorを使用して学習 指定したディレクトリの直下に分類ごとにサブディレクトリが必要
        # epoch_sizeは、サンプル数が少ないときは水増し用のオプションをONにして、多めにする
        '''
        batch_size = batch_size if batch_size != 0 else self.BATCH_SIZE
        epoch_size = epoch_size if epoch_size != 0 else self.EPOCH_SIZE
        try:
            modelDir = os.path.join(self.DEFAULT_DIR, modelDir)
            validDir = os.path.join(self.DEFAULT_DIR, validDir)

            # オプションを有効にすることでバリエーションを増やして学習できる
            train_datagen = ImageDataGenerator(
                rescale=1.0 / 255,
                shear_range=0.2,
                zoom_range=0.2,
                horizontal_flip=True,
                rotation_range=10,
                width_shift_range=0.2,
                height_shift_range=0.2,
                vertical_flip=True,
                featurewise_center=False,
                samplewise_center=False,
                #featurewise_std_normalization=False,
                #samplewise_std_normalization=False,
                #zca_whitening=False,
                #channel_shift_range=0.,
                #fill_mode='nearest',
                #cval=0.,
                #dim_ordering=K.image_dim_ordering()
                )
            # ここは3/4でいい
            steps_coefficient = 1 / 4 * 3

            # validation_generator用設定
            valid_datagen = ImageDataGenerator(
                rescale=1.0 / 255,
            )

            train_generator = train_datagen.flow_from_directory(
                modelDir,
                target_size=(self.IMAGE_SIZE, self.IMAGE_SIZE),
                batch_size=batch_size,
                class_mode='categorical',
                shuffle=True
            )

            validation_generator = valid_datagen.flow_from_directory(
                validDir,
                target_size=(self.IMAGE_SIZE, self.IMAGE_SIZE),
                batch_size=batch_size,
                class_mode='categorical',
                shuffle=True
            )

            # sample数/バッチサイズ すべてのファイルを読み込めるサイズにする？
            train_steps_per_epoch:int = math.floor(len(train_generator.filenames) / batch_size * steps_coefficient)
            valid_steps_per_epoch:int = math.floor(len(validation_generator.filenames) / batch_size  * steps_coefficient)

            if mode_add:
                model = self.addModelFromShape(len(train_generator.class_indices))
            elif mode_bin:
                model = self.addModelFromShapeSigmoid()
            else:
                model = self.createModelFromShape(len(train_generator.class_indices))

            model.summary()
            
            def scheduler(epoch, lr):
                if epoch < 10:
                    return lr
                else:
                    return lr * tf.math.exp(-0.1)

            lr_decay = tf.keras.callbacks.LearningRateScheduler(scheduler)

            hist = model.fit(
                train_generator,
                steps_per_epoch=train_steps_per_epoch, #デフォルトは計算してくれる(sample数/バッチサイズ)
                validation_data=validation_generator,
                validation_steps=valid_steps_per_epoch, #デフォルトは計算してくれる(sample数/バッチサイズ)
                epochs=epoch_size,
                verbose=1,
                shuffle=True,
                callbacks=[tf.keras.callbacks.EarlyStopping(monitor='accuracy', min_delta=0.001, patience=40, restore_best_weights=True)]
            )

            logger.info(hist.history)

            model.save(self.hdf5_file)

            if not mode_bin:
                class_indices = train_generator.class_indices
                class_indices = {v: k for k, v in class_indices.items()}
                with open(self.class_file, 'w', encoding='utf-8') as cf:
                    json.dump(class_indices, cf, ensure_ascii=False)

        except Exception as e:
            logger.error('model not create')
            logger.error(e)


    # 学習モデルの作成と保存
    def saveModel(self, modelDir, batch_size=0, epoch_size=0, mode_add=False):
        batch_size = batch_size if batch_size != 0 else self.BATCH_SIZE
        epoch_size = epoch_size if epoch_size != 0 else self.EPOCH_SIZE
        try:
            categories = []
            xy = self.createTrainData(modelDir, categories)
            x_train, x_test, y_train, y_test = xy

            # 正規化
            self.x_train:float = x_train * 1.0 / 255
            self.x_test:float = x_test * 1.0 / 255
            self.y_train = np_utils.to_categorical(y_train, len(categories))
            self.y_test = np_utils.to_categorical(y_test, len(categories))

            # 学習モデルの保存
            if mode_add:
                model = self.addModelFromShape(len(categories))
            else:
                model = self.createModelFromShape(len(categories))
            model.summary()

            model.fit(self.x_train, self.y_train, batch_size=batch_size, epochs=epoch_size)
            model.save(self.hdf5_file)

            class_indices = {str(k): v for k, v in enumerate(categories)}
            with open(self.class_file, 'w', encoding='utf-8') as cf:
                json.dump(class_indices, cf, ensure_ascii=False)

            # テスト
            score = model.evaluate(self.x_test, self.y_test)
            logger.info(f"loss: {score[0]}")
            logger.info(f"accuracy: {score[1]}")

        except Exception as e:
            logger.error('model not create')
            logger.error(e)


    # 入力画像の予測
    def predictFromFilesBin(self, filenames, size=5):
        if len(filenames) == 0:
            return []

        X = list(map(self.createDataFromImage, filenames))
        img_predict = np.array(X)

        model = load_model(self.hdf5_file)
        model.summary()

        logger.info(f"predict start : {len(img_predict)}")
        result_predict = model.predict(img_predict, batch_size=self.BATCH_SIZE)

        result = []
        for i in range(len(img_predict)):
            predict_array = (result_predict[i]).tolist()
            predict_array = (np.array(predict_array)).argsort()[::-1]

            result.append(
                [os.path.basename(os.path.dirname(filenames[i])),
                os.path.basename(filenames[i]), 
                result_predict[i][0]])

        return result


    # 入力画像の予測
    def predictFromFiles(self, filenames, size=5):
        if len(filenames) == 0:
            return []

        X = list(map(self.createDataFromImage, filenames))
        img_predict = np.array(X)

        model = load_model(self.hdf5_file)
        model.summary()

        logger.info(f"predict start : {len(img_predict)}")
        result_predict = model.predict(img_predict, batch_size=self.BATCH_SIZE)
        #result_predict_classes = model.predict_classes(img_predict)
        result_predict_classes = np.argmax(result_predict, axis=1)

        with open(self.class_file, 'r', encoding='utf-8') as cf:
            class_indices = json.load(cf)
        logger.debug(class_indices)

        result = []
        for i in range(len(img_predict)):
            predict_array = (result_predict[i]).tolist()
            predict_array = (np.array(predict_array)).argsort()[::-1]

            result.append(
                [os.path.basename(os.path.dirname(filenames[i])),
                os.path.basename(filenames[i]), 
                class_indices[str(result_predict_classes[i])],
                class_indices[str(predict_array[1])],
                class_indices[str(predict_array[2])],
                result_predict[i],
                result_predict[i][result_predict_classes[i]]])

        return result


    # 入力画像の予測
    def predictFromDirs(self, imageDir, size=5):
        logger.info(f"target:{imageDir}")
        pre_datagen = ImageDataGenerator(
            rescale=1.0 / 255,
        )

        pre_generator = pre_datagen.flow_from_directory(
            imageDir,
            target_size=(self.IMAGE_SIZE, self.IMAGE_SIZE),
            batch_size=self.BATCH_SIZE,
            class_mode=None,
            shuffle=False
        )

        if len(pre_generator.filenames) == 0:
            return []

        logger.info(f"target files:{len(pre_generator.filenames)}")

        model = load_model(self.hdf5_file)
        model.summary()

        logger.info(f"loaded Model")

        result_predict = model.predict_generator(pre_generator, verbose=1, steps=10)
        result_predict_classes = np.argmax(result_predict, axis=1)

        with open(self.class_file, 'r', encoding='utf-8') as cf:
            class_indices = json.load(cf)
        print(class_indices)
        #print(result_predict)
        print(len(result_predict))

        result =[]
        filenames = pre_generator.filenames
        for i in range(len(filenames)):
            predict_array = (result_predict[i]).tolist()
            predict_array = (np.array(predict_array)).argsort()[::-1]
            #print(predict_array)

            result.append(
                [os.path.basename(os.path.dirname(filenames[i])),
                os.path.basename(filenames[i]), 
                class_indices[str(result_predict_classes[i])],
                class_indices[str(predict_array[1])],
                class_indices[str(predict_array[2])],
                result_predict[i]])
        return result


