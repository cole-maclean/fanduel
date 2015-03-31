delimiter $$

CREATE TABLE `atbat` (
  `game_id` varchar(30) NOT NULL,
  `half` varchar(10) DEFAULT NULL,
  `inning` int(11) DEFAULT NULL,
  `num` int(11) NOT NULL,
  `b` int(11) DEFAULT NULL,
  `s` int(11) DEFAULT NULL,
  `o` int(11) DEFAULT NULL,
  `score` char(1) DEFAULT NULL,
  `batter` int(11) DEFAULT NULL,
  `stand` char(1) DEFAULT NULL,
  `b_height` varchar(5) DEFAULT NULL,
  `pitcher` int(11) DEFAULT NULL,
  `p_throws` char(1) DEFAULT NULL,
  `des` varchar(500) CHARACTER SET utf8 DEFAULT NULL,
  `des_es` varchar(500) CHARACTER SET utf8 DEFAULT NULL,
  `event` varchar(200) CHARACTER SET utf8 DEFAULT NULL,
  `event2` varchar(200) CHARACTER SET utf8 DEFAULT NULL,
  `event3` varchar(200) CHARACTER SET utf8 DEFAULT NULL,
  `event4` varchar(200) CHARACTER SET utf8 DEFAULT NULL,
  `home_team_runs` int(11) DEFAULT NULL,
  `away_team_runs` int(11) DEFAULT NULL,
  `start_tfs` int(11) DEFAULT NULL,
  `start_tfs_zulu` varchar(25) DEFAULT NULL,
  `event_num` varchar(45) DEFAULT NULL,
  `event_es` varchar(45) DEFAULT NULL,
  `event2_es` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`game_id`,`num`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1$$
delimiter $$

CREATE TABLE `fd_table_contests` (
  `idFD_table_contests` int(11) NOT NULL AUTO_INCREMENT,
  `contest_id` varchar(45) DEFAULT NULL,
  `entry_id` varchar(45) DEFAULT NULL,
  `sport` varchar(45) DEFAULT NULL,
  `entryFee` int(11) DEFAULT NULL,
  `size` int(11) DEFAULT NULL,
  `entriesData` int(11) DEFAULT NULL,
  `startTime` varchar(45) DEFAULT NULL,
  `avg_top_wins` double DEFAULT NULL,
  `gameType` varchar(255) DEFAULT NULL,
  `strat_params` varchar(255) DEFAULT NULL,
  `startString` varchar(45) DEFAULT NULL,
  `game_id` varchar(45) DEFAULT NULL,
  `timestamp` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`idFD_table_contests`)
) ENGINE=InnoDB AUTO_INCREMENT=651 DEFAULT CHARSET=latin1$$

delimiter $$

CREATE TABLE `fetch_log` (
  `id` int(11) NOT NULL,
  `game_day` datetime DEFAULT NULL,
  `type` varchar(50) DEFAULT NULL,
  `output` text,
  `processed` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1$$

delimiter $$

CREATE TABLE `game` (
  `game_id` varchar(30) NOT NULL,
  `game_type` char(1) NOT NULL,
  `local_game_time` varchar(10) DEFAULT NULL,
  `game_pk` int(11) DEFAULT NULL,
  `game_time_et` varchar(10) DEFAULT NULL,
  `home_sport_code` varchar(10) DEFAULT NULL,
  `home_id` int(11) DEFAULT NULL,
  `home_team_code` varchar(3) DEFAULT NULL,
  `home_fname` varchar(30) DEFAULT NULL,
  `home_sname` varchar(30) DEFAULT NULL,
  `home_wins` int(11) DEFAULT NULL,
  `home_loss` int(11) DEFAULT NULL,
  `away_id` int(11) DEFAULT NULL,
  `away_team_code` varchar(3) DEFAULT NULL,
  `away_fname` varchar(50) DEFAULT NULL,
  `away_sname` varchar(50) DEFAULT NULL,
  `away_wins` int(11) DEFAULT NULL,
  `away_loss` int(11) DEFAULT NULL,
  `status_ind` char(1) DEFAULT NULL,
  `date` date DEFAULT NULL,
  `day` varchar(3) DEFAULT NULL,
  `stadium_id` int(11) DEFAULT NULL,
  `stadium_name` varchar(40) DEFAULT NULL,
  `stadium_location` varchar(30) DEFAULT NULL,
  PRIMARY KEY (`game_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1$$

delimiter $$

CREATE TABLE `hist_player_data` (
  `DataID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `Sport` varchar(45) DEFAULT NULL,
  `Player` varchar(45) DEFAULT NULL,
  `GameID` bigint(20) DEFAULT NULL,
  `Team` varchar(45) DEFAULT NULL,
  `Stat1` varchar(45) DEFAULT NULL,
  `Stat2` varchar(45) DEFAULT NULL,
  `Stat3` varchar(45) DEFAULT NULL,
  `Stat4` varchar(45) DEFAULT NULL,
  `Stat5` varchar(45) DEFAULT NULL,
  `Stat6` varchar(45) DEFAULT NULL,
  `Stat7` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`DataID`)
) ENGINE=InnoDB AUTO_INCREMENT=67990 DEFAULT CHARSET=latin1$$

delimiter $$

CREATE TABLE `historical_weather` (
  `station_id` varchar(45) DEFAULT NULL,
  `date` date DEFAULT NULL,
  `data_type` varchar(45) DEFAULT NULL,
  `data_value` varchar(45) DEFAULT NULL,
  `dummy1` varchar(45) DEFAULT NULL,
  `dummy2` varchar(45) DEFAULT NULL,
  `dummy3` varchar(45) DEFAULT NULL,
  `time` varchar(45) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1$$

delimiter $$

CREATE TABLE `hitchart` (
  `hit_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `game_id` varchar(30) NOT NULL,
  `des` varchar(25) DEFAULT NULL,
  `x` decimal(7,3) DEFAULT NULL,
  `y` decimal(7,3) DEFAULT NULL,
  `batter` int(11) DEFAULT NULL,
  `pitcher` int(11) DEFAULT NULL,
  `type` char(1) DEFAULT NULL,
  `team` enum('H','A') DEFAULT NULL,
  `inning` tinyint(4) DEFAULT NULL,
  PRIMARY KEY (`hit_id`)
) ENGINE=InnoDB AUTO_INCREMENT=52893 DEFAULT CHARSET=latin1$$

delimiter $$

CREATE TABLE `last` (
  `type` varchar(5) DEFAULT NULL,
  `year` int(11) DEFAULT NULL,
  `month` int(11) DEFAULT NULL,
  `day` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1$$

delimiter $$

CREATE TABLE `pitch` (
  `game_id` varchar(30) NOT NULL,
  `num` int(11) NOT NULL DEFAULT '0',
  `pitcher` int(11) DEFAULT NULL,
  `batter` int(11) DEFAULT NULL,
  `b` tinyint(4) DEFAULT NULL,
  `s` tinyint(4) DEFAULT NULL,
  `des` varchar(100) DEFAULT NULL,
  `id` int(11) NOT NULL DEFAULT '0',
  `type` varchar(3) NOT NULL,
  `x` decimal(7,3) DEFAULT NULL,
  `y` decimal(7,3) DEFAULT NULL,
  `on_1b` int(11) DEFAULT NULL,
  `on_2b` int(11) DEFAULT NULL,
  `on_3b` int(11) DEFAULT NULL,
  `sv_id` varchar(20) DEFAULT NULL,
  `start_speed` decimal(7,3) DEFAULT NULL,
  `end_speed` decimal(7,3) DEFAULT NULL,
  `sz_top` decimal(7,3) DEFAULT NULL,
  `sz_bot` decimal(7,3) DEFAULT NULL,
  `pfx_x` decimal(7,3) DEFAULT NULL,
  `pfx_z` decimal(7,3) DEFAULT NULL,
  `px` decimal(7,3) DEFAULT NULL,
  `pz` decimal(7,3) DEFAULT NULL,
  `x0` decimal(7,3) DEFAULT NULL,
  `y0` decimal(7,3) DEFAULT NULL,
  `z0` decimal(7,3) DEFAULT NULL,
  `vx0` decimal(7,3) DEFAULT NULL,
  `vy0` decimal(7,3) DEFAULT NULL,
  `vz0` decimal(7,3) DEFAULT NULL,
  `ax` decimal(7,3) DEFAULT NULL,
  `ay` decimal(7,3) DEFAULT NULL,
  `az` decimal(7,3) DEFAULT NULL,
  `break_y` decimal(7,3) DEFAULT NULL,
  `break_angle` decimal(7,3) DEFAULT NULL,
  `break_length` decimal(7,3) DEFAULT NULL,
  `pitch_type` char(2) DEFAULT NULL,
  `type_confidence` decimal(7,3) DEFAULT NULL,
  `spin_dir` decimal(7,3) DEFAULT NULL,
  `spin_rate` decimal(7,3) DEFAULT NULL,
  `zone` tinyint(4) DEFAULT NULL,
  PRIMARY KEY (`game_id`,`num`,`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1$$

delimiter $$

CREATE TABLE `scoring` (
  `event` varchar(45) DEFAULT NULL,
  `batterpoints` decimal(10,2) DEFAULT NULL,
  `pitcherpoints` decimal(10,2) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1$$

delimiter $$

CREATE TABLE `player` (
  `team` varchar(3) DEFAULT NULL,
  `id` int(11) NOT NULL,
  `pos` varchar(3) DEFAULT NULL,
  `type` enum('pitcher','batter') DEFAULT NULL,
  `first_name` varchar(30) DEFAULT NULL,
  `current_position` varchar(3) DEFAULT NULL,
  `last_name` varchar(30) DEFAULT NULL,
  `jersey_number` varchar(2) DEFAULT NULL,
  `height` varchar(5) DEFAULT NULL,
  `weight` int(11) DEFAULT NULL,
  `bats` varchar(3) DEFAULT NULL,
  `throws` varchar(3) DEFAULT NULL,
  `dob` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1$$

delimiter $$

CREATE TABLE `hist_performance` (
  `Entry_Id` varchar(45) NOT NULL,
  `Sport` varchar(45) DEFAULT NULL,
  `Date` varchar(45) DEFAULT NULL,
  `Title` varchar(45) DEFAULT NULL,
  `SalaryCap` varchar(45) DEFAULT NULL,
  `Score` double DEFAULT NULL,
  `Opp Score` varchar(45) DEFAULT NULL,
  `Position` int(11) DEFAULT NULL,
  `Entries` bigint(20) DEFAULT NULL,
  `Opponent` varchar(45) DEFAULT NULL,
  `Entry Cost` double DEFAULT NULL,
  `Winnings` double DEFAULT NULL,
  `Link` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`Entry_Id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1$$


