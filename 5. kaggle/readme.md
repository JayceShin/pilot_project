## Kaggle

    ⭐ 사내 캐글대회에 참여하여 총 38팀 중 2등을 수상하였습니다.
    
![캐글_순위](https://user-images.githubusercontent.com/31294995/134780170-ec38e969-0c0b-4b86-9b70-c84012fe6109.PNG)

📖 **목차**

[1. EDA](#1-EDA)

[2. 데이터 전처리](#2-데이터-전처리)

[3. 모델링](#3-모델링)

[4. 수행 결과](#4-수행-결과)
***
## 1 EDA

### Class Imbalanced

    데이터 분포 확인을 통해 Class Imbalance임을 파악하였습니다.   
    
![캐글_임밸런스](https://user-images.githubusercontent.com/31294995/134780171-acf6d445-93cb-4b7a-8002-6247a4f444d5.PNG)

***
## 2 데이터 전처리

### Category Encoding

    Label이 총 5개의 카테고리로 구성되었기에 int형으로 인코딩하였습니다.   

Encoding
```python
# Train Data의 Category를 숫자형 데이터로 변환
for i in range(len(train_data['Category'])):
    if(train_data['Category'][i] == 'N'):
        train_data['Category'][i] = 0
    elif(train_data['Category'][i] == 'S'):
        train_data['Category'][i] = 1
    elif(train_data['Category'][i] == 'V'):
        train_data['Category'][i] = 2
    elif(train_data['Category'][i] == 'F'):
        train_data['Category'][i] = 3
    elif(train_data['Category'][i] == 'Q'):
        train_data['Category'][i] = 4
```

### OverSampling

    EDA 과정을 통해 Imbalanced Data임을 확인하였으므로 OverSampling을 진행하였습니다.   

OverSampling
```python
# Oversampling을 위해 가장 큰 클래스를 기준으로 각 클래스별 반복수를 설정
con = train_data.sample(frac=1, axis=0)
val = con.values

x = val[:,1:]
y = val[:,0].astype(int)

x_temp = []
count_temp = []

for label in range(5):
    x_i = x[y == label]
    x_temp.append(x_i)
    count_temp.append(len(x_i))
    
counts = (np.floor(max(count_temp) / np.array(count_temp))).astype(int)

# 반복 수 만큼 데이터를 늘리는 Oversampling 적용

for label in range(5):
    count = counts[label]
    if label == 0:
        x_bal = x_temp[label]
        y_bal = np.zeros((count_temp[label])).astype(int)
        count -= 1

    for j in range(count):
        x_bal = np.concatenate((x_bal, x_temp[label]), axis=0)
        y_bal = np.concatenate((y_bal, np.zeros((count_temp[label])).astype(int) + label))
```

***
## 3 모델링

    분류문제이며 시퀀스 데이터이기 때문에 1D CNN을 통해 분류기를 구성하였습니다.   

네트워크 구성(Keras)   

```python
# CNN 모델 정의

def network(X_train,y_train,X_test,y_test):
    
    im_shape=(X_train.shape[1],1)
    inputs_cnn=Input(shape=(im_shape), name='inputs_cnn')
    
    conv1_1=Convolution1D(64, (6), activation='relu', input_shape=im_shape)(inputs_cnn)
    conv1_1=BatchNormalization()(conv1_1)
    pool1=MaxPool1D(pool_size=(3), strides=(2), padding="same")(conv1_1)
    
    conv2_1=Convolution1D(64, (3), activation='relu', input_shape=im_shape)(pool1)
    conv2_1=BatchNormalization()(conv2_1)
    pool2=MaxPool1D(pool_size=(2), strides=(2), padding="same")(conv2_1)
    
    conv3_1=Convolution1D(64, (3), activation='relu', input_shape=im_shape)(pool2)
    conv3_1=BatchNormalization()(conv3_1)
    pool3=MaxPool1D(pool_size=(2), strides=(2), padding="same")(conv3_1)

    flatten=Flatten()(pool3)
    
    dense_end1 = Dense(64, activation='relu')(flatten)
    dense_end2 = Dense(32, activation='relu')(dense_end1)
    main_output = Dense(5, activation='softmax', name='main_output')(dense_end2)
    
    model = Model(inputs= inputs_cnn, outputs=main_output)
    model.compile(optimizer='adam', loss='categorical_crossentropy',metrics = ['accuracy'])
    
    callbacks = [EarlyStopping(monitor='val_loss', patience=8),
             ModelCheckpoint(filepath='best_model.h6', monitor='val_loss', save_best_only=True)]

    history=model.fit(X_train, y_train,epochs=100,callbacks=callbacks, batch_size=128,validation_data=(X_test,y_test))
    model.load_weights('best_model.h6')
    return(model,history)
```

***
## 4 수행 결과

train vs val Accuracy & Loss  
![캐글_로스](https://user-images.githubusercontent.com/31294995/134780172-2df0071f-5848-40a5-b1f7-2ce0b2d06454.PNG)

***
