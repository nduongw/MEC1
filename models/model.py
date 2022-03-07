import torch.nn as nn
import torch
 
class Model(nn.Module):
    def __init__(self, Config):
        super().__init__()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.Config = Config
        self.in_channels1 = Config.get('cnn').get('in_channels1')
        self.in_channels2 = Config.get('cnn').get('in_channels2')
        self.in_channels3 = Config.get('cnn').get('in_channels3')

        self.out_channels1 = Config.get('cnn').get('out_channels1')
        self.out_channels2 = Config.get('cnn').get('out_channels2')
        self.out_channels3 = Config.get('cnn').get('out_channels3')

        self.kernel_size1 = Config.get('cnn').get('kernel_size1')
        self.kernel_size2 = Config.get('cnn').get('kernel_size2')
        self.kernel_size3 = Config.get('cnn').get('kernel_size3')

        self.hidden_size = Config.get('lstm').get('hidden_size')
        self.num_layers = Config.get('lstm').get('num_layers')


        # 3 1D-Conv layer
        self.conv1 = nn.Conv2d(in_channels=self.in_channels1, out_channels=self.out_channels1, kernel_size=self.kernel_size1, padding='same')
        self.conv2 = nn.Conv2d(in_channels=self.in_channels2, out_channels=self.out_channels2, kernel_size=self.kernel_size2, padding='same')
        self.conv3 = nn.Conv2d(in_channels=self.in_channels3, out_channels=self.out_channels3, kernel_size=self.kernel_size3, padding='same')

        # batchnorm
        self.batchnorm1 = nn.BatchNorm2d(self.out_channels1)
        self.batchnorm2 = nn.BatchNorm2d(self.out_channels2)
        self.batchnorm3 = nn.BatchNorm2d(self.out_channels3)

        self.relu = nn.ReLU()
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.flatten = nn.Flatten()

        self.fc_v = nn.Linear(in_features=self.hidden_size, out_features=1)
    
    def shared_layers(self, x):

        # x = (n_env, num_frame, 2, h, w)
        self.height_map = x.size()[3]
        self.width_map = x.size()[4]
        self.batchsize = x.size()[0]

        hidden = self.init_hidden()
        out_cnn = []

        for i in range(self.Config.get("num_frame")):
            xi = x[:,i,:,:,:]    # xi = (n_env, 2, h, w)
            out_conv1 = self.pool(self.relu(self.batchnorm1(self.conv1(xi))))
            out_conv2 = self.pool(self.relu(self.batchnorm2(self.conv2(out_conv1))))
            out_conv3 = self.pool(self.relu(self.batchnorm3(self.conv3(out_conv2))))
            out_flatten = self.flatten(out_conv3)       # (n_env, n)
            out_cnn.append(torch.unsqueeze(out_flatten, dim=1)) # (n_env, 1, n)
        
        self.lstm_input_size = out_cnn[0].size()[2]     # n
        self.lstm = nn.LSTM(input_size= self.lstm_input_size, hidden_size=self.hidden_size, num_layers=self.num_layers, batch_first=True).to(self.device)

        in_lstm = torch.cat(out_cnn, 1)  # in_lstm = (n_env, num_frame, h/8 * w/8 * out_channel3)
        out_lstm, hidden = self.lstm(in_lstm, hidden)

        out_shared_layers = out_lstm[:,-1,:]    # out_shared_layers = (n_env, hidden_size)

        return out_shared_layers

    def pi(self, x):
        out_shared_layers = self.shared_layers(x)

        self.fc_pi = nn.Linear(in_features=self.hidden_size, out_features=self.height_map*self.width_map).to(self.device)

        out_fc = self.fc_pi(out_shared_layers).view(-1, self.height_map, self.width_map)
        prob = nn.Sigmoid()(out_fc)
        return prob

    def v(self, x):
        out_shared_layers = self.shared_layers(x)
        value = self.fc_v(out_shared_layers)

        return value

    def init_hidden(self) :
        h0 = torch.zeros((self.num_layers, self.batchsize, self.hidden_size)).to(self.device)
        c0 = torch.zeros((self.num_layers, self.batchsize, self.hidden_size)).to(self.device)
        hidden = (h0,c0)
        return hidden
