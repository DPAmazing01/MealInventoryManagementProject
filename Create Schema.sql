-- ===========================================================
-- CSC540 PROJECT 1 – FINALIZED SCHEMA + TRIGGERS/PROCEDURES/VIEWS
-- ===========================================================

DROP DATABASE IF EXISTS inventory_management;
CREATE DATABASE inventory_management;
USE inventory_management;

-- ===========================================================
-- USERS
-- ===========================================================
CREATE TABLE `User` (
    user_id VARCHAR(10) PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    first_name VARCHAR(30),
    last_name VARCHAR(30),
    contact_info VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    user_type ENUM('MANUFACTURER','SUPPLIER','VIEWER') NOT NULL,
    CONSTRAINT name_length CHECK (LENGTH(first_name) >= 2 AND LENGTH(last_name) >= 2)
);

-- ===========================================================
-- CATEGORIES
-- ===========================================================
CREATE TABLE Category (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    CONSTRAINT category_name_length CHECK (LENGTH(name) >= 2)
);

-- ===========================================================
-- PRODUCTS
-- ===========================================================
CREATE TABLE Product (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    product_number VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    category_id INT NOT NULL,
    manufacturer_id VARCHAR(10) NOT NULL,
    description TEXT,
    standard_batch_units INT NOT NULL,
    FOREIGN KEY (category_id) REFERENCES Category(category_id),
    FOREIGN KEY (manufacturer_id) REFERENCES User(user_id) ON DELETE CASCADE,
    CONSTRAINT product_name_length CHECK (LENGTH(name) >= 2),
    CONSTRAINT valid_batch_size CHECK (standard_batch_units > 0)
);

-- ===========================================================
-- INGREDIENTS
-- ===========================================================
CREATE TABLE Ingredient (
    ingredient_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type ENUM('ATOMIC','COMPOUND') NOT NULL,
    description TEXT,
    CONSTRAINT ingredient_name_length CHECK (LENGTH(name) >= 2)
);

-- ===========================================================
-- SUPPLIERS
-- ===========================================================
CREATE TABLE Supplier (
    supplier_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    user_id VARCHAR(10) NULL,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE SET NULL,
    CONSTRAINT supplier_name_length CHECK (LENGTH(name) >= 2)
);

-- ===========================================================
-- SUPPLIER–INGREDIENT RELATION
-- ===========================================================
CREATE TABLE SupplierIngredient (
    supplier_id INT NOT NULL,
    ingredient_id INT NOT NULL,
    can_supply BOOLEAN NOT NULL,
    PRIMARY KEY (supplier_id, ingredient_id),
    FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES Ingredient(ingredient_id) ON DELETE CASCADE
);

-- ===========================================================
-- INGREDIENT FORMULATIONS
-- ===========================================================
CREATE TABLE IngredientFormulation (
    formulation_id INT AUTO_INCREMENT PRIMARY KEY,
    ingredient_id INT NOT NULL,
    supplier_id INT NOT NULL,
    version_no INT NOT NULL,
    effective_start DATE NOT NULL,
    effective_end DATE NULL,
    price_per_pack DECIMAL(10,2) NOT NULL,
    pack_size DECIMAL(10,2) NOT NULL,
    is_active BOOLEAN NOT NULL,
    FOREIGN KEY (ingredient_id) REFERENCES Ingredient(ingredient_id) ON DELETE CASCADE,
    FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id) ON DELETE CASCADE,
    CONSTRAINT valid_date_range CHECK (effective_end IS NULL OR effective_end > effective_start),
    CONSTRAINT positive_price CHECK (price_per_pack > 0),
    CONSTRAINT positive_pack_size CHECK (pack_size > 0),
    UNIQUE KEY unique_formulation_version (ingredient_id,supplier_id,version_no)
);

-- ===========================================================
-- FORMULATION MATERIALS
-- ===========================================================
CREATE TABLE FormulationMaterials (
    formulation_id INT NOT NULL,
    ingredient_id INT NOT NULL,
    qty DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (formulation_id, ingredient_id),
    FOREIGN KEY (formulation_id) REFERENCES IngredientFormulation(formulation_id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES Ingredient(ingredient_id) ON DELETE CASCADE,
    CONSTRAINT positive_material_qty CHECK (qty > 0)
);

-- ===========================================================
-- RECIPE PLANS
-- ===========================================================
CREATE TABLE RecipePlan (
    recipe_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    version_no INT NOT NULL,
    creation_date DATE NOT NULL,
    is_active BOOLEAN NOT NULL,
    notes TEXT,
    replaced_by_id INT NULL,
    FOREIGN KEY (product_id) REFERENCES Product(product_id) ON DELETE CASCADE,
    FOREIGN KEY (replaced_by_id) REFERENCES RecipePlan(recipe_id),
    UNIQUE KEY unique_product_version (product_id,version_no)
);

-- ===========================================================
-- PRODUCT BILL OF MATERIALS
-- ===========================================================
CREATE TABLE ProductBOM (
    product_id INT NOT NULL,
    ingredient_id INT NOT NULL,
    qty DECIMAL(10,2) NOT NULL,
    recipe_id INT NULL,
    UNIQUE KEY uq_product_bom (product_id, ingredient_id, recipe_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES Ingredient(ingredient_id) ON DELETE CASCADE,
    FOREIGN KEY (recipe_id) REFERENCES RecipePlan(recipe_id) ON DELETE SET NULL,
    CONSTRAINT positive_bom_qty CHECK (qty > 0)
);

-- ===========================================================
-- INGREDIENT BATCHES
-- ===========================================================
CREATE TABLE IngredientBatch (
    lot_number VARCHAR(100) PRIMARY KEY,
    ingredient_id INT NOT NULL,
    supplier_id INT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    unit_cost DECIMAL(10,4) NOT NULL,
    expiration_date DATE NOT NULL,
    intake_date DATE NOT NULL,
    on_hand_quantity DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (ingredient_id) REFERENCES Ingredient(ingredient_id) ON DELETE CASCADE,
    FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id) ON DELETE CASCADE,
    CONSTRAINT valid_expiration CHECK (DATEDIFF(expiration_date,intake_date) >= 90),
    CONSTRAINT positive_quantity CHECK (quantity > 0),
    CONSTRAINT ib_positive_unit_cost CHECK (unit_cost > 0),
    CONSTRAINT valid_on_hand CHECK (on_hand_quantity >= 0 AND on_hand_quantity <= quantity)
);

-- ===========================================================
-- PRODUCT BATCHES
-- ===========================================================
CREATE TABLE ProductBatch (
    lot_number VARCHAR(100) PRIMARY KEY,
    product_id INT NOT NULL,
    manufacturer_id VARCHAR(10) NOT NULL,
    recipe_id INT NOT NULL,
    produced_qty INT NOT NULL,
    produced_at DATE NOT NULL,
    expiration_date DATE NOT NULL,
    total_batch_cost DECIMAL(12,2) NOT NULL,
    per_unit_cost DECIMAL(10,4) NOT NULL,
    FOREIGN KEY (product_id) REFERENCES Product(product_id) ON DELETE CASCADE,
    FOREIGN KEY (manufacturer_id) REFERENCES User(user_id),
    FOREIGN KEY (recipe_id) REFERENCES RecipePlan(recipe_id) ON DELETE RESTRICT,
    CONSTRAINT positive_produced_quantity CHECK (produced_qty > 0),
    CONSTRAINT positive_total_cost CHECK (total_batch_cost >= 0),
    CONSTRAINT pb_positive_unit_cost CHECK (per_unit_cost >= 0)
);

-- ===========================================================
-- PRODUCTION CONSUMPTION
-- ===========================================================
CREATE TABLE ProductionConsumption (
    product_batch VARCHAR(100) NOT NULL,
    ingredient_lot VARCHAR(100) NOT NULL,
    qty DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (product_batch, ingredient_lot),
    FOREIGN KEY (product_batch) REFERENCES ProductBatch(lot_number) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_lot) REFERENCES IngredientBatch(lot_number) ON DELETE CASCADE,
    CONSTRAINT positive_consumption_qty CHECK (qty > 0)
);

-- ===========================================================
-- CONFLICT PAIRS
-- ===========================================================
CREATE TABLE ConflictPairs (
    ingredient_a INT NOT NULL,
    ingredient_b INT NOT NULL,
    reason TEXT,
    severity ENUM('WARNING','CRITICAL') NOT NULL,
    PRIMARY KEY (ingredient_a,ingredient_b),
    FOREIGN KEY (ingredient_a) REFERENCES Ingredient(ingredient_id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_b) REFERENCES Ingredient(ingredient_id) ON DELETE CASCADE
);

-- ===========================================================
-- HEALTH RISK RULES
-- ===========================================================
CREATE TABLE HealthRiskRule (
    rule_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    severity ENUM('LOW','MEDIUM','HIGH','CRITICAL') NOT NULL,
    action_type ENUM('LOG','BLOCK') NOT NULL,
    is_active BOOLEAN NOT NULL,
    CONSTRAINT rule_name_length CHECK (LENGTH(name) >= 2)
);

-- ===========================================================
-- INGREDIENT HEALTH RISK
-- ===========================================================
CREATE TABLE IngredientHealthRisk (
    ingredient_health_risk_id INT AUTO_INCREMENT PRIMARY KEY,
    ingredient_id INT NOT NULL,
    rule_id INT NOT NULL,
    threshold_quantity DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (ingredient_id) REFERENCES Ingredient(ingredient_id) ON DELETE CASCADE,
    FOREIGN KEY (rule_id) REFERENCES HealthRiskRule(rule_id) ON DELETE CASCADE,
    UNIQUE KEY unique_ingredient_rule (ingredient_id,rule_id),
    CONSTRAINT positive_threshold CHECK (threshold_quantity > 0)
);

-- ===========================================================
-- RECALL EVENTS
-- ===========================================================
CREATE TABLE RecallEvent (
    recall_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_id INT NOT NULL,
    ingredient_id INT NULL,
    ingredient_lot VARCHAR(100) NULL,
    recall_date DATE NOT NULL,
    recall_end_date DATE NULL,
    reason TEXT NOT NULL,
    recall_type ENUM('INGREDIENT','LOT','BOTH') NOT NULL,
    is_active BOOLEAN NOT NULL,
    FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES Ingredient(ingredient_id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_lot) REFERENCES IngredientBatch(lot_number) ON DELETE CASCADE,
    CONSTRAINT recall_type_check CHECK (
        (recall_type='INGREDIENT' AND ingredient_id IS NOT NULL) OR
        (recall_type='LOT' AND ingredient_lot IS NOT NULL) OR
        (recall_type='BOTH' AND ingredient_id IS NOT NULL AND ingredient_lot IS NOT NULL)
    )
);

-- ===========================================================
-- INDEXES
-- ===========================================================
CREATE INDEX idx_product_manufacturer ON Product(manufacturer_id);
CREATE INDEX idx_product_category ON Product(category_id);
CREATE INDEX idx_ingredient_type ON Ingredient(type);
CREATE INDEX idx_ingredient_batch_expiry ON IngredientBatch(ingredient_id,expiration_date,on_hand_quantity);
CREATE INDEX idx_ingredient_batch_supplier ON IngredientBatch(supplier_id);
CREATE INDEX idx_product_batch_date ON ProductBatch(produced_at);
CREATE INDEX idx_formulation_active ON IngredientFormulation(ingredient_id,is_active,effective_start,effective_end);
CREATE INDEX idx_recipe_active ON RecipePlan(product_id,is_active);

-- ===========================================================
-- SEQUENCE TABLE (Helper for IngredientBatch lot numbers)
-- ===========================================================
CREATE TABLE IF NOT EXISTS SeqIngredientBatch (
  seq_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (seq_id)
) ENGINE=InnoDB;

-- ===========================================================
-- TRIGGERS
-- ===========================================================

DELIMITER $$

CREATE TRIGGER bi_PreventDuplicateConflictPairs
BEFORE INSERT ON ConflictPairs
FOR EACH ROW
BEGIN
  DECLARE tmp INT;
  IF NEW.ingredient_a = NEW.ingredient_b THEN
    SIGNAL SQLSTATE '45000'
	  SET MESSAGE_TEXT = '❌ Ingredients must be different';
  END IF;
  IF NEW.ingredient_a > NEW.ingredient_b THEN
    SET tmp = NEW.ingredient_a;
	SET NEW.ingredient_a = NEW.ingredient_b;
	SET NEW.ingredient_b = tmp;
  END IF;
END$$

CREATE TRIGGER bi_IngredientBatch_compute_lot
BEFORE INSERT ON IngredientBatch
FOR EACH ROW
BEGIN
    DECLARE next_seq INT;
    -- Default on-hand = quantity
    IF NEW.on_hand_quantity IS NULL THEN
        SET NEW.on_hand_quantity = NEW.quantity;
    END IF;
    -- Compute next sequence number for this ingredient + supplier
    SELECT COALESCE(
        MAX(
            CAST(SUBSTRING(lot_number,
                LOCATE('B', lot_number) + 1
            ) AS UNSIGNED)
        ), 0
    ) + 1
    INTO next_seq
    FROM IngredientBatch
    WHERE ingredient_id = NEW.ingredient_id
      AND supplier_id = NEW.supplier_id;
    -- Generate lot number in sample format
    IF NEW.lot_number IS NULL OR NEW.lot_number = '' THEN
        SET NEW.lot_number = CONCAT(
            NEW.ingredient_id, '-', NEW.supplier_id, '-B',
            LPAD(next_seq, 4, '0')
        );
    END IF;
END$$

CREATE TRIGGER bi_PreventExpiredConsumption
BEFORE INSERT ON ProductionConsumption
FOR EACH ROW
BEGIN
  DECLARE exp_date DATE;
  SELECT expiration_date INTO exp_date FROM IngredientBatch WHERE lot_number = NEW.ingredient_lot;
  IF exp_date < CURDATE() THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = '❌ Cannot consume expired ingredient batch.';
  END IF;
END$$

CREATE TRIGGER ai_UpdateOnHandAfterConsumption
AFTER INSERT ON ProductionConsumption
FOR EACH ROW
BEGIN
  UPDATE IngredientBatch
     SET on_hand_quantity = on_hand_quantity - NEW.qty
   WHERE lot_number = NEW.ingredient_lot;
  IF (SELECT on_hand_quantity FROM IngredientBatch WHERE lot_number = NEW.ingredient_lot) < 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = '❌ Ingredient batch on-hand cannot go below zero.';
  END IF;
END$$
DELIMITER ;

-- ===========================================================
-- STORED PROCEDURES
-- ===========================================================

DELIMITER $$

CREATE PROCEDURE RecordProductionBatch (
  IN p_product_id INT,
  IN p_manufacturer_id VARCHAR(10),
  IN p_recipe_id INT,
  IN p_produced_qty INT,
  IN p_produced_at DATE,
  IN p_expiration_date DATE,
  IN p_consumptions JSON
)
BEGIN
  DECLARE done INT DEFAULT 0;
  DECLARE v_lot VARCHAR(100);
  DECLARE v_qty DECIMAL(10,2);
  DECLARE v_cost DECIMAL(10,4);
  DECLARE v_total_cost DECIMAL(12,2) DEFAULT 0;
  DECLARE v_batch_id VARCHAR(100);
  -- Variables for Lot Number Generation
  DECLARE v_next_seq INT;
  DECLARE v_sequential_part VARCHAR(10);

  DECLARE cur CURSOR FOR 
    SELECT JSON_UNQUOTE(JSON_EXTRACT(j.value, '$.lot')),
           JSON_EXTRACT(j.value, '$.qty')
      FROM JSON_TABLE(p_consumptions, "$[*]" COLUMNS (value JSON PATH "$")) j;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

  START TRANSACTION;

  -- 1. Generate Batch ID
  SELECT COALESCE(
      MAX(
          CAST(SUBSTRING(lot_number,
              LOCATE('B', lot_number) + 1
          ) AS UNSIGNED)
      ), 0
  ) + 1
  INTO v_next_seq
  FROM ProductBatch
  WHERE product_id = p_product_id
    AND manufacturer_id = p_manufacturer_id;
    
  -- Generate the lot number
  SET v_sequential_part = CONCAT('B', LPAD(v_next_seq, 4, '0'));
  SET v_batch_id = CONCAT(p_product_id, '-', p_manufacturer_id, '-', v_sequential_part);

  -- 2. INSERT into ProductBatch FIRST (Creates the parent record)
  -- Temporarily set costs to 0. They will be updated after cost calculation.
  INSERT INTO ProductBatch (
    lot_number, product_id, manufacturer_id, recipe_id,
    produced_qty, produced_at, expiration_date,
    total_batch_cost, per_unit_cost
  )
  VALUES (
    v_batch_id, p_product_id, p_manufacturer_id, p_recipe_id,
    p_produced_qty, p_produced_at, p_expiration_date,
    0, 0
  );

  OPEN cur;
  read_loop: LOOP
    FETCH cur INTO v_lot, v_qty;
    IF done THEN LEAVE read_loop; END IF;

    -- Get Unit Cost from the IngredientBatch before consumption
    SELECT unit_cost INTO v_cost FROM IngredientBatch WHERE lot_number = v_lot;

    -- Update Ingredient Inventory
    UPDATE IngredientBatch SET on_hand_quantity = on_hand_quantity - v_qty WHERE lot_number = v_lot;

    -- Calculate total cost
    SET v_total_cost = v_total_cost + (v_cost * v_qty);

    -- 3. INSERT into ProductionConsumption (Child record insertion now succeeds)
    INSERT INTO ProductionConsumption (product_batch, ingredient_lot, qty)
    VALUES (v_batch_id, v_lot, v_qty);

  END LOOP;
  CLOSE cur;

  -- 4. UPDATE ProductBatch with final calculated costs (used CAST for precision)
  UPDATE ProductBatch
  SET total_batch_cost = v_total_cost,
      per_unit_cost = v_total_cost / CAST(p_produced_qty AS DECIMAL(10, 4))
  WHERE lot_number = v_batch_id;

  COMMIT;
END$$

CREATE PROCEDURE TraceRecall (
  IN p_ingredient_id INT,
  IN p_lot_number VARCHAR(100)
)
BEGIN
  IF p_lot_number IS NOT NULL THEN
    SELECT pb.lot_number AS product_batch, pb.product_id, pb.produced_at, ic.ingredient_lot
      FROM ProductBatch pb
      JOIN ProductionConsumption ic ON pb.lot_number = ic.product_batch
     WHERE ic.ingredient_lot = p_lot_number;
  ELSE
    SELECT pb.lot_number AS product_batch, pb.product_id, pb.produced_at, ib.ingredient_id
      FROM ProductBatch pb
      JOIN ProductionConsumption ic ON pb.lot_number = ic.product_batch
      JOIN IngredientBatch ib ON ic.ingredient_lot = ib.lot_number
     WHERE ib.ingredient_id = p_ingredient_id;
  END IF;
END$$

CREATE PROCEDURE EvaluateHealthRisk (
  IN p_product_batch VARCHAR(100)
)
BEGIN
  IF EXISTS (
    SELECT 1
      FROM ProductionConsumption pc1
      JOIN ProductionConsumption pc2
        ON pc1.product_batch = pc2.product_batch AND pc1.ingredient_lot <> pc2.ingredient_lot
      JOIN IngredientBatch ib1 ON pc1.ingredient_lot = ib1.lot_number
      JOIN IngredientBatch ib2 ON pc2.ingredient_lot = ib2.lot_number
      JOIN ConflictPairs cp ON cp.ingredient_a = LEAST(ib1.ingredient_id, ib2.ingredient_id)
                           AND cp.ingredient_b = GREATEST(ib1.ingredient_id, ib2.ingredient_id)
     WHERE cp.severity = 'CRITICAL'
  ) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = '⚠️ Health Risk: Critical conflict detected between ingredients.';
  END IF;
END$$
DELIMITER ;

-- ===========================================================
-- VIEWS
-- ===========================================================
CREATE OR REPLACE VIEW vw_active_supplier_formulations AS
SELECT f.formulation_id, i.name AS ingredient_name, s.name AS supplier_name,
       f.price_per_pack, f.pack_size, f.effective_start, f.effective_end
  FROM IngredientFormulation f
  JOIN Ingredient i ON f.ingredient_id = i.ingredient_id
  JOIN Supplier s ON f.supplier_id = s.supplier_id
 WHERE f.is_active = TRUE
   AND (f.effective_end IS NULL OR f.effective_end >= CURDATE());

CREATE OR REPLACE VIEW vw_flattened_product_bom AS
SELECT p.product_id, p.name AS product_name, i.ingredient_id,
       i.name AS ingredient_name, pb.qty AS ingredient_qty, c.name AS category_name
  FROM ProductBOM pb
  JOIN Product p ON pb.product_id = p.product_id
  JOIN Ingredient i ON pb.ingredient_id = i.ingredient_id
  JOIN Category c ON p.category_id = c.category_id;

CREATE OR REPLACE VIEW vw_recent_health_violations AS
SELECT pb.lot_number AS product_batch, pb.product_id, hr.name AS rule_name,
       hr.severity, hr.action_type, pb.produced_at
  FROM ProductBatch pb
  JOIN ProductionConsumption pc ON pb.lot_number = pc.product_batch
  JOIN IngredientBatch ib ON pc.ingredient_lot = ib.lot_number
  JOIN IngredientHealthRisk ihr ON ib.ingredient_id = ihr.ingredient_id
  JOIN HealthRiskRule hr ON ihr.rule_id = hr.rule_id
 WHERE hr.is_active = TRUE
   AND pb.produced_at >= (CURDATE() - INTERVAL 30 DAY)
   AND hr.severity IN ('HIGH','CRITICAL');

SELECT '✅ Schema, Triggers, Procedures, and Views created successfully.' AS status;
