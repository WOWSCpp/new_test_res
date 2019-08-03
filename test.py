import pprint
import os
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

class IostatAnalyzer(object):
	def __init__(self):
		self.res = {
			"rand_write" : {
				"high_speed_elapsed_time": 0,
				"high_speed_avg_iops": 0,
				"low_speed_avg_iops": 0
			},

			"rand_read" : {
				"high_speed_elapsed_time": 0,
				"high_speed_avg_iops": 0,
				"low_speed_avg_iops": 0
			}
		}


	def iostat(self, file_name, rw="r"):
		ramp_time = 300
		fobj = open(file_name)
		tmp_high, tmp_low, all_data_r, all_data_w = [], [], [], []
		for line in fobj.readlines():
			if line.startswith("nvme0n1"):
				ramp_time -= 1
				if ramp_time > 0: 
					if rw == "r":
						all_data_r.append((0, 0))
					elif rw == "w":
						all_data_w.append((0, 0))
					continue
				contents = line.split()
				if rw == "r":
					cache_read_iops = float(contents[3])
					cache_read_bw   = float(contents[5])
					all_data_r.append((cache_read_iops, cache_read_bw))
					if cache_read_iops > 100000.0:
						self.res["rand_read"]["high_speed_elapsed_time"] += 1
						tmp_high.append(cache_read_iops)
					else:
						tmp_low.append(cache_read_iops)
				elif rw == "w":
					cache_write_iops = float(contents[4])
					cache_write_bw   = float(contents[6])
					all_data_w.append((cache_write_iops, cache_write_bw))
					if cache_write_iops > 100000.0:
						self.res["rand_write"]["high_speed_elapsed_time"] += 1
						tmp_high.append(cache_write_iops)
					else:
						tmp_low.append(cache_write_iops)

		if rw == "r":
			self.res["rand_read"]["high_speed_avg_iops"] = sum(tmp_high) / len(tmp_high) if len (tmp_high) > 0 else 0
			self.res["rand_read"]["low_speed_avg_iops"] = sum(tmp_low) / len(tmp_low) if len (tmp_low) > 0 else 0
		elif rw == "w":
			self.res["rand_write"]["high_speed_avg_iops"] = sum(tmp_high) / len(tmp_high) if len (tmp_high) > 0 else 0
			self.res["rand_write"]["low_speed_avg_iops"] = sum(tmp_low) / len(tmp_low) if len (tmp_low) > 0 else 0
		
		fobj.close()

		if rw == "r":
			return all_data_r
		elif rw == "w":
			return all_data_w


	def log_res(self):
		pprint.pprint(self.res)


	def draw_iostat_iops_and_bw(self, data):
		plt.figure(figsize=(16, 8))
		time = [i for i in range(len(data))]
		iops = list(map(lambda x : x[0], data))
		bw   = list(map(lambda x : (x[1] / 1024), data))
		

		plt.subplot(1,2,1)
		plt.plot(time, iops, color='pink', label='iops', linewidth=1.0)
		plt.legend()
		plt.xlabel('time', fontsize=20)
		plt.ylabel('iostat iops', fontsize=20)
		plt.ylim(ymin=0)

		plt.subplot(1,2,2)
		plt.plot(time, bw, color='blue', label='bw', linewidth=1.0)
		plt.legend() 
		plt.xlabel('time', fontsize=20)
		plt.ylabel('iostat bandwidth in MB', fontsize=20)
		plt.ylim(ymin=0)
		plt.savefig("iostat_iops")
		#plt.show()
		


class FioAnalyzer(object):
	def __init__(self):
		pass
	

	def get_all_files(self):
		path = '.'
		iops_files, bw_files, lat_files = [], [], []
		for r, d, f in os.walk(path):
			for file in f:
				if '.log' in file:
					if 'iops' in file:
						iops_files.append(os.path.join(r, file))
					elif 'bw' in file:
						bw_files.append(os.path.join(r, file))
					elif '_lat' in file:
						lat_files .append(os.path.join(r, file))
		return iops_files, bw_files, lat_files


	def draw_fio_iops_and_bw(self, iops_files, bw_files):
		
		iops_table = {}
		for idx, file_name in enumerate(iops_files):
			fobj = open(file_name)
			iops_list = []
			for line in fobj.readlines():
				iops = int(line.split(",")[1])
				iops_list.append(iops)
			iops_table[str(idx)] = iops_list

		vals = list(iops_table.values())
		_sum = [0 for i in range(len(vals[0]))]
		min_len = min(list(map(lambda x : len(x), vals)))
		for i in range(min_len):
			for j in range(len(vals)):
				_sum[i] += vals[j][i]
		iops_table["sum"] = _sum
		time = [i for i in range(min_len)]
		plt.figure(figsize=(16, 8))
		plt.subplot(1,2,1)
		plt.plot(time, iops_table["sum"][:min_len], color='pink', linewidth=1.0)
		plt.legend()
		plt.xlabel('time', fontsize=20)
		plt.ylabel('fio iops', fontsize=20)
		plt.ylim(ymin=0)


		bw_table = {}
		for idx, file_name in enumerate(bw_files):
			fobj = open(file_name)
			bw_list = []
			for line in fobj.readlines():
				iops = int(line.split(",")[1])
				bw_list.append(iops)
			bw_table[str(idx)] = bw_list

		vals = list(bw_table.values())
		_sum = [0 for i in range(len(vals[0]))]
		min_len = min(list(map(lambda x : len(x), vals)))
		for i in range(min_len):
			for j in range(len(vals)):
				_sum[i] += (vals[j][i] / 1024)
		bw_table["sum"] = _sum
		time = [i for i in range(min_len)]

		plt.subplot(1,2,2)
		plt.plot(time, bw_table["sum"][:min_len], color='blue', linewidth=1.0)
		plt.legend()
		plt.xlabel('time', fontsize=20)
		plt.ylabel('fio bandwidth in MB', fontsize=20)
		plt.ylim(ymin=0)

		plt.savefig("fio_iops")
		#plt.show()
		


	def draw_fio_lat(self, lat_files):
		
		lat_table = {}
		for idx, file_name in enumerate(lat_files):
			fobj = open(file_name)
			lat_list = []
			for line in fobj.readlines():
				iops = int(line.split(",")[1])
				lat_list.append(iops)
			lat_table[str(idx)] = lat_list

		vals = list(lat_table.values())
		_sum = [0 for i in range(len(vals[0]))]
		min_len = min(list(map(lambda x : len(x), vals)))
		for i in range(min_len):
			for j in range(len(vals)):
				_sum[i] += vals[j][i]
		lat_table["sum"] = _sum
		time = [i for i in range(min_len)]

		plt.figure(figsize=(10, 5))
		plt.plot(time, lat_table["sum"][:min_len], color='red', linewidth=1.0)
		plt.legend()
		plt.xlabel('time', fontsize=20)
		plt.ylabel('fio latency in ns', fontsize=20)
		plt.ylim(ymin=0)

		plt.savefig("latency")
		#plt.show()
		




class BcacheAnalyzer(object):
	def __init__(self, file_name):
		self.config = {
			"cache"   : "cache info",
			"backing" : "backing info",
		}
		
		self.cache_info   = {
			"block_size" : "0",
			"bucket_size" : "0", 
			"btree_size" : [],
			"cache_available_percent" : [],
			"average_key_size" : []
		}

		self.backing_info = {
			"bypassed" : [],
			"cache_hits" : [], 
			"cache_hit_ratio" : [],
			"cache_misses" : []
		}

		self.data_size_with_M = set()
		self.data_size_with_k = set()
		self.parse_records(file_name)

	def parse_records(self, file_name):
		with open(file_name, "r") as f:
			for i, line in enumerate(f):
				if line.startswith(self.config["cache"]):
					content = line[line.index("block_size") : ].replace("\n", "") # cache info starts with "block_size"
					each_dict = dict(zip(self.cache_info.keys(), [c.split(":")[1].strip() for c in content.split(",")]))
					self.cache_info["block_size"] = each_dict["block_size"]
					self.cache_info["bucket_size"] = each_dict["bucket_size"]
					for key in self.cache_info.keys():
						if key is not "block_size" and key is not "bucket_size":
							val = each_dict[key]
							if val.count("M") != 0:
								self.data_size_with_M.add(key)
								num = float(val.split("M")[0]) * 1024 * 1024
							elif val.count("k") != 0:
								self.data_size_with_k.add(key)
								num = float(val.split("k")[0]) * 1024
							else:
								num = float(val)
							self.cache_info[key].append(num)

				elif line.startswith(self.config["backing"]):
					content = line[line.index("bypassed") : ].replace("\n", "") # backing info starts with "bypassed"
					each_dict = dict(zip(self.backing_info.keys(), [c.split(":")[1] for c in content.split(",")]))
					for key in self.backing_info.keys():
						if key is not "block_size" and key is not "bucket_size":
							val = each_dict[key]
							if val.count("M") != 0:
								self.data_size_with_M.add(key)
								num = float(val.split("M")[0]) * 1024 * 1024
							elif val.count("k") != 0:
								self.data_size_with_k.add(key)
								num = float(val.split("k")[0]) * 1024
							else:
								num = float(val)
							self.backing_info[key].append(num)

	def calculate_results(self):
		print("Cache information:")
		for key, val in self.cache_info.items():
			if key is "block_size":
				print (key, " : ", val)
			elif key is "bucket_size":
				print (key, " : ", val)
			elif key in self.data_size_with_M:
				print ("Average ", key, " : ", str(round(float(sum(val) / len(val) / 1024 / 1024), 1)) + "M")
			elif key in self.data_size_with_k:
				print ("Average ", key, " : ", str(round(float(sum(val) / len(val) / 1024), 1)) + "k")
			else:
				print("Average ", key, " : ", int(sum(val) / len(val)))

		print ()
		print("Backing information:")
		for key, val in self.backing_info.items():
			if key in self.data_size_with_M:
				print ("Average ", key, " : ", str(round(float(sum(val) / len(val) / 1024 / 1024), 1)) + "M")
			elif key in self.data_size_with_k:
				print ("Average ", key, " : ", str(round(float(sum(val) / len(val) / 1024), 1)) + "k")
			else:
				print("Average ", key, " : ", int(sum(val) / len(val)))

	def draw_cache_hit_ratio(self):
		plt.figure(figsize=(10, 5))
		time = [i for i in range(len(self.backing_info["cache_hit_ratio"]))]
		plt.plot(time, self.backing_info["cache_hit_ratio"], color='blue', linewidth=1.0)
		plt.legend() 
  
		plt.xlabel('time', fontsize=20)
		plt.ylabel('cache_hit_ratio', fontsize=20)
		plt.ylim(ymin=0)

		plt.savefig("hit_ratio")
		#plt.show()
		


if __name__ == '__main__':
	path1  = "C:\\Users\\kaixinliu\\Desktop\\new_test_res\\96g_4g_4k_4%_area_100%hot_wb_randread\\stable"
	
	path2  = "C:\\Users\\kaixinliu\\Desktop\\new_test_res\\96g_4g_4k_5%_area_100%hot_wb_randread\\stable"
	
	path3  = "C:\\Users\\kaixinliu\\Desktop\\new_test_res\\96g_4g_4k_6%_area_100%hot_wb_randread\\stable"
	
	path4  = "C:\\Users\\kaixinliu\\Desktop\\new_test_res\\96g_4g_4k_7%_area_100%hot_wb_randread\\stable"
	
	path5  = "C:\\Users\\kaixinliu\\Desktop\\new_test_res\\96g_4g_4k_8%_area_100%hot_wb_randread\\stable"
	
	path6  = "C:\\Users\\kaixinliu\\Desktop\\new_test_res\\96g_4g_4k_9%_area_100%hot_wb_randread\\stable"

	os.chdir(path16)


	f = FioAnalyzer()
	iops_files, bw_files, lat_files = f.get_all_files()
	f.draw_fio_iops_and_bw(iops_files, bw_files)
	f.draw_fio_lat(lat_files)

	b = BcacheAnalyzer("bcache_stat.txt")
	b.draw_cache_hit_ratio()

	i = IostatAnalyzer()
	data = i.iostat("iostat.txt", "r")
	i.draw_iostat_iops_and_bw(data)
	#i.log_res()

