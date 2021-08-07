CREATE TABLE `backup_history` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `started` datetime NOT NULL,
  `finished` datetime DEFAULT NULL,
  `status` int NOT NULL DEFAULT '-1',
  `dryrun` enum('YES','NO') NOT NULL,
  `srcdir` varchar(255) NOT NULL,
  `refdir` varchar(255) NOT NULL,
  `tgtdir` varchar(255) NOT NULL,
  `directories_processed` int unsigned NOT NULL DEFAULT '0',
  `directories_skipped` int unsigned NOT NULL DEFAULT '0',
  `files_copied` int unsigned NOT NULL DEFAULT '0',
  `bytes_copied` bigint unsigned NOT NULL DEFAULT '0',
  `file_attributes_copied` int unsigned NOT NULL DEFAULT '0',
  `symlinks_copied` int unsigned NOT NULL DEFAULT '0',
  `links_created` int unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

CREATE TABLE `backup_copied_file` (
  `backup_id` int unsigned NOT NULL,
  `srcpath` varchar(255) NOT NULL,
  `filesize` bigint unsigned NOT NULL,
  KEY `backup_id` (`backup_id`),
  CONSTRAINT `backup_copied_file_ibfk_1` FOREIGN KEY (`backup_id`) REFERENCES `backup_history` (`id`)
) ENGINE=InnoDB;
