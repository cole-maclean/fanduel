delimiter $$
DROP TABLE IF EXISTS fd_table_contests;

CREATE TABLE `fd_table_contests` (
  `idFD_table_contests` int(11) NOT NULL AUTO_INCREMENT,
  `contest_id` varchar(45) DEFAULT NULL,
  `entry_id` varchar(45) DEFAULT NULL,
  `sport` varchar(45) DEFAULT NULL,
  `entryFee` int(11) DEFAULT NULL,
  `size` int(11) DEFAULT NULL,
  `entriesData` int(11) DEFAULT NULL,
  `startTime` varchar(45) DEFAULT NULL,
  `entry_wins_dict` blob,
  `gameType` varchar(255) DEFAULT NULL,
  `strat_params` varchar(255) DEFAULT NULL,
  `startString` varchar(45) DEFAULT NULL,
  `game_id` varchar(45) DEFAULT NULL,
  `timestamp` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`idFD_table_contests`)
) ENGINE=InnoDB AUTO_INCREMENT=755 DEFAULT CHARSET=latin1$$

delimiter $$
DROP TABLE IF EXISTS hist_performance;

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

delimiter $$

DROP TABLE IF EXISTS hist_player_data;

CREATE TABLE `hist_player_data` (
  `Sport` varchar(45) NOT NULL,
  `Player` varchar(45) NOT NULL,
  `GameID` varchar(255) NOT NULL,
  `Position` varchar(45) DEFAULT NULL,
  `Team` varchar(45) DEFAULT NULL,
  `Player_Type` varchar(45) NOT NULL,
  `Stat1` varchar(45) DEFAULT NULL,
  `Stat2` varchar(45) DEFAULT NULL,
  `Stat3` varchar(45) DEFAULT NULL,
  `Stat4` varchar(45) DEFAULT NULL,
  `Stat5` varchar(45) DEFAULT NULL,
  `Stat6` varchar(45) DEFAULT NULL,
  `Stat7` varchar(45) DEFAULT NULL,
  `Stat8` varchar(45) DEFAULT NULL,
  `Stat9` varchar(45) DEFAULT NULL,
  `Stat10` varchar(45) DEFAULT NULL,
  `Stat11` varchar(45) DEFAULT NULL,
  `Stat12` varchar(45) DEFAULT NULL,
  `Stat13` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`Player`,`GameID`,`Player_Type`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1$$





