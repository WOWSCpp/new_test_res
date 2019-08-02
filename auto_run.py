import os
import sys
import time

class AutoRun(object):
	def __init__(self):
		self.warmup 		= True
		self.now_size 		= 4
		self.max_size 		= 9
		self.task_count 	= 0
		self.warmup_time 	= 10
		self.stable_time 	= 10

	def wait_and_check(self, t, status):
		time.sleep(t)
		assert(status == 0)

	def reset_bcache(self):
		status = os.system('sh ~/test_script/release.sh')
		self.wait_and_check(5, status)
		
		status = os.system('sh ~/test_script/bcache.sh')
		self.wait_and_check(5, status)

	def change_parameter(self):
		# change size every two tasks
		# change runtime every one task

		size = str(self.now_size) + "g"
		status = os.system("sed -i 's/size=.*/size=%s/' cache_size_experiment.fio" % size)
		self.wait_and_check(1, status)
		
		if self.warmup:
			runtime = str(self.warmup_time)
		else:
			runtime = str(self.stable_time)
		status = os.system("sed -i 's/runtime=.*/runtime=%s/' cache_size_experiment.fio" % runtime)
		self.wait_and_check(1, status)


	def run_task(self):
		status = os.system('sh ~/test_script/test1.sh')
		if self.warmup:
			wait_time = self.warmup_time + 10
		else:
			wait_time = self.stable_time + 10
		self.wait_and_check(wait_time, status)


	def copy_and_upload_data(self):
		# first cd to the git path
		root_dir = "~/results/auto_test_res/" + str(self.now_size) + "g"
		if self.warmup:
			root_dir += "/warmup"
		else:
			root_dir += "/stable"

		os.chdir(root_dir)
		status = os.system("cd %s" % root_dir)
		self.wait_and_check(1, status)

		# second do the things with git
		_size   = str(self.now_size) + "g"
		_status = "warmup" is self.warmup else "stable"
		status = os.system('cp ~/test_script/*.log .')
		self.wait_and_check(1, status)
		status = os.system('cp ~/results/*.txt .')
		self.wait_and_check(1, status)
		status = os.system('git add *')
		self.wait_and_check(1, status)
		status = os.system('git commit -m "%s-%s"' % (_size, _status))
		self.wait_and_check(5, status)
		status = os.system('git push')
		self.wait_and_check(5, status)

		# last cd to the script path
		os.chdir("~/test_script/")
		status = os.system("cd ~/test_script/")
		self.wait_and_check(1, status)


	def main_loop(self):
		while self.now_size < self.max_size:
			self.reset_bcache()
			self.change_parameter()
			self.run_task()
			self.copy_and_upload_data()

			self.task_count += 1
			if task_count % 2 == 0:
				self.now_size += 1

			if self.warmup:
				self.warmup = False
			else:
				self.warmup = True

if __name__ == '__main__':
	run = AutoRun()
	run.main_loop()
