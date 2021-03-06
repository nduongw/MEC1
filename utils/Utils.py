from matplotlib.pyplot import sci
import torch
import scipy.stats
import yaml

with open('config/hyperparameter.yaml') as f:
    Config = yaml.safe_load(f)

def generate_map(Config):
    road = []

    for i in range(Config.get('road_number')):
        roadi = torch.rand(Config.get('road_length'), Config.get('road_width_list')[i])
        for u in range (roadi.size()[0]):
            for v in range(roadi.size()[1]):
                if roadi[u, v] > Config.get('generate_prob'):
                    roadi[u, v] = 1
                else : 
                    roadi[u, v] = 0
        road.append(roadi)

        if i < Config.get('road_number') - 1:
            roadi = torch.zeros(Config.get('road_length'), Config.get('road_dis_list')[i])
            road.append(roadi)

    new_road = torch.hstack([*road])

    return new_road

# def generate_map(Config, roadmap):
#     for i in range(Config.get('road_number')):
#         x_delta = Config.get('x_max')[i] - Config.get('x_min')[i]
#         y_delta = Config.get('road_length')

#         area_total = x_delta * y_delta
        
#         num_points = scipy.stats.poisson(Config.get('lambda_list')[i] * area_total).rvs()
#         # print(num_points)
#         # print('--------')
#         xx = x_delta * scipy.stats.uniform.rvs(0, 1, ((num_points, 1))) + Config.get('x_min')[i]
#         yy = y_delta * scipy.stats.uniform.rvs(0, 1, ((num_points, 1)))
        
#         x_idx = xx.astype(int)
#         y_idx = yy.astype(int)
        
#         for x, y in zip(x_idx, y_idx):
#             # print(f'{x.item()} -- {y.item()}')
#             roadmap[y.item(), x.item()] = 1
        

def count_car(road):
    car_list = []
    for i in range(road.shape[0]):
        for j in range(road.shape[1]):
            if road[i, j].item() == 1:
                car_list.append([i, j])

    return car_list

def set_cover_radius(road, car_list):
    cover_map = torch.zeros(road.shape[0], road.shape[1])

    for car in car_list:
        for i in range (max(car[0] - Config.get('cover_radius'), 0), 1 + min(car[0] + Config.get('cover_radius'), road.shape[0] - 1)):
            for j in range(max(car[1] - Config.get('cover_radius'), 0),1 + min(car[1] + Config.get('cover_radius'), road.shape[1] - 1)):
                cover_map[i, j] = 1
                
    return cover_map

def calc_overlap(car_list):
    overlap_map = torch.zeros(Config.get('road_length'), Config.get('road_width'))
    
    for car in car_list:
        for i in range (max(car[0] - Config.get('cover_radius'), 0), 1 + min(car[0] + Config.get('cover_radius'), Config.get('road_length') - 1)):
            for j in range(max(car[1] - Config.get('cover_radius'), 0),1 + min(car[1] + Config.get('cover_radius'), Config.get('road_width') - 1)):
                    overlap_map[i, j] += 1
    
    overlap = torch.count_nonzero(torch.where(overlap_map > 1, torch.ones_like(overlap_map), torch.zeros_like(overlap_map))).item()          
    return overlap

def generate_air_quality_map(road, Config):
    car_list = count_car(road)
    cover_map = set_cover_radius(road, car_list)
    
    return cover_map

def get_coordinate_dis(Config):
    list_coord = []
    a = 0
    for i in range(Config.get('road_number') - 1):
        if i == 0:
            # list_coord.append(Config.roadWidthList[i])
            a += Config.get('road_width_list')[i]
            for j in range(a, a + Config.get('road_dis_list')[i]):
                list_coord.append(j)
            
        else:
            a += Config.get('road_width_list')[i] + Config.get('road_dis_list')[i - 1]
            for j in range(a, a + Config.get('road_dis_list')[i]):    
                list_coord.append(j)

    return list_coord
    