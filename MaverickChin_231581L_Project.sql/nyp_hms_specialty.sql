-- MySQL dump 10.13  Distrib 8.0.44, for Win64 (x86_64)
--
-- Host: localhost    Database: nyp_hms
-- ------------------------------------------------------
-- Server version	8.0.44

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `specialty`
--

DROP TABLE IF EXISTS `specialty`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `specialty` (
  `specialty_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `is_in_service` tinyint(1) NOT NULL,
  PRIMARY KEY (`specialty_id`)
) ENGINE=InnoDB AUTO_INCREMENT=40 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `specialty`
--

LOCK TABLES `specialty` WRITE;
/*!40000 ALTER TABLE `specialty` DISABLE KEYS */;
INSERT INTO `specialty` VALUES (1,'Anaesthesiology',1),(2,'Cardiology',1),(3,'Cardiothoracic Surgery',1),(4,'Dermatology',1),(5,'Diagnostic Radiology',1),(6,'Emergency Medicine',1),(7,'Endocrinology',1),(8,'Family Medicine',1),(9,'Gastroenterology',1),(10,'General Surgery',1),(11,'Geriatric Medicine',1),(12,'Haematology',1),(13,'Hand Surgery',1),(14,'Infectious Diseases',1),(15,'Internal Medicine',1),(16,'Medical Oncology',1),(17,'Neurology',1),(18,'Neurosurgery',1),(19,'Nuclear Medicine',1),(20,'Obstetrics & Gynaecology',1),(21,'Occupational Medicine',1),(22,'Ophthalmology',1),(23,'Orthopaedic Surgery',1),(24,'Otorhinolaryngology/ENT',1),(25,'Paediatric Medicine',1),(26,'Paediatric Surgery',1),(27,'Pathology',1),(28,'Plastic Surgery',1),(29,'Psychiatry',1),(30,'Public Health',1),(31,'Radiation Oncology',1),(32,'Rehabilitation Medicine',1),(33,'Renal Medicine',1),(34,'Respiratory Medicine',1),(35,'Rheumatology',1),(36,'Urology',1),(37,'Intensive Care Medicine',1),(38,'Sports Medicine',1),(39,'Palliative Medicine',1);
/*!40000 ALTER TABLE `specialty` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-02-01 23:31:28
