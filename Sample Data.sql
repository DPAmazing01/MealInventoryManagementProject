USE inventory_management;

-- ===========================================================
-- CLEAN START
-- ===========================================================
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE ProductionConsumption;
TRUNCATE TABLE ProductBatch;
TRUNCATE TABLE IngredientBatch;
TRUNCATE TABLE ProductBOM;
TRUNCATE TABLE RecipePlan;
TRUNCATE TABLE FormulationMaterials;
TRUNCATE TABLE IngredientFormulation;
TRUNCATE TABLE SupplierIngredient;
TRUNCATE TABLE Supplier;
TRUNCATE TABLE IngredientHealthRisk;
TRUNCATE TABLE HealthRiskRule;
TRUNCATE TABLE ConflictPairs;
TRUNCATE TABLE Ingredient;
TRUNCATE TABLE Product;
TRUNCATE TABLE Category;
TRUNCATE TABLE `User`;
SET FOREIGN_KEY_CHECKS = 1;

-- ===========================================================
-- USERS
-- ===========================================================
INSERT INTO `User` (user_id, username, first_name, last_name, contact_info, password_hash, user_type)
VALUES
('MFG001', 'john_smith', 'John', 'Smith', 'john@factory.com', 'hash', 'MANUFACTURER'),
('MFG002', 'alice_lee', 'Alice', 'Lee', 'alice@factory.com', 'hash', 'MANUFACTURER'),
('SUP001', 'jane_doe', 'Jane', 'Doe', 'jane@supplier.com', 'hash', 'SUPPLIER'),
('VIEW001', 'bob_johnson', 'Bob', 'Johnson', 'bob@viewer.com', 'hash', 'VIEWER');

-- ===========================================================
-- CATEGORIES
-- ===========================================================
INSERT INTO Category (category_id, name)
VALUES
(2, 'Dinners'),
(3, 'Sides');

-- ===========================================================
-- PRODUCTS
-- ===========================================================
INSERT INTO Product (product_id, product_number, name, category_id, manufacturer_id, description, standard_batch_units)
VALUES
(100, 'P-100', 'Steak Dinner', 2, 'MFG001', 'Prepared steak dinner', 500),
(101, 'P-101', 'Mac & Cheese', 3, 'MFG002', 'Creamy macaroni side', 300);


-- ===========================================================
-- INGREDIENTS
-- ===========================================================
INSERT INTO Ingredient (ingredient_id, name, type, description)
VALUES
(101, 'Salt', 'ATOMIC', 'Seasoning'),
(102, 'Pepper', 'ATOMIC', 'Black pepper'),
(104, 'Sodium Phosphate', 'ATOMIC', 'Food additive'),
(106, 'Beef Steak', 'ATOMIC', 'Meat cut'),
(108, 'Pasta', 'ATOMIC', 'Durum wheat pasta'),
(201, 'Seasoning Blend', 'COMPOUND', 'Mix of spices'),
(301, 'Super Seasoning', 'COMPOUND', 'Enhanced seasoning blend');

-- ===========================================================
-- SUPPLIERS
-- ===========================================================
INSERT INTO Supplier (supplier_id, name, user_id)
VALUES
(20, 'Supplier A', 'SUP001'),
(21, 'Supplier B', NULL);

-- ===========================================================
-- SUPPLIER-INGREDIENT RELATION
-- ===========================================================
INSERT INTO SupplierIngredient (supplier_id, ingredient_id, can_supply)
VALUES
(20, 101, TRUE),
(20, 102, TRUE),
(20, 104, TRUE),
(20, 106, TRUE),
(20, 108, TRUE),
(20, 201, TRUE),
(21, 101, TRUE),
(21, 102, TRUE);

-- ===========================================================
-- INGREDIENT FORMULATIONS
-- ===========================================================
INSERT INTO IngredientFormulation
(formulation_id, ingredient_id, supplier_id, version_no, effective_start, effective_end, price_per_pack, pack_size, is_active)
VALUES
(1, 201, 20, 1, '2025-01-01', '2025-06-30', 20.0, 8.0, TRUE);


-- ===========================================================
-- FORMULATION MATERIALS
-- ===========================================================
INSERT INTO FormulationMaterials (formulation_id, ingredient_id, qty)
VALUES
(1, 101, 6.0),
(1, 102, 2.0);

-- ===========================================================
-- RECIPE PLANS
-- ===========================================================
INSERT INTO RecipePlan (recipe_id, product_id, version_no, creation_date, is_active, notes, replaced_by_id)
VALUES
(1, 100, 1, '2025-01-01', TRUE, 'Initial recipe for Steak Dinner', NULL),
(2, 101, 1, '2025-01-01', TRUE, 'Initial recipe for Mac & Cheese', NULL);


-- ===========================================================
-- PRODUCT BILL OF MATERIALS
-- ===========================================================
INSERT INTO ProductBOM (product_id, ingredient_id, qty, recipe_id)
VALUES
(100, 106, 6.0, 1),
(100, 201, 0.2, 1),
(101, 108, 7.0, 2),
(101, 101, 0.5, 2),
(101, 102, 2.0, 2);

-- ===========================================================
-- INGREDIENT BATCHES
-- ===========================================================
INSERT INTO IngredientBatch (lot_number, ingredient_id, supplier_id, quantity, unit_cost, expiration_date, intake_date, on_hand_quantity)
VALUES
('101-20-B0001', 101, 20, 1000, 0.10, '2025-11-15', '2025-07-01', 1000),
('101-21-B0001', 101, 21, 800, 0.08, '2025-12-05', '2025-07-01', 800),
('101-20-B0002', 101, 20, 500, 0.10, '2025-12-01', '2025-07-01', 500),
('101-20-B0003', 101, 20, 500, 0.10, '2025-12-15', '2025-07-01', 500),
('102-20-B0001', 102, 20, 1200, 0.30, '2025-12-15', '2025-07-01', 1200),
('106-20-B0005', 106, 20, 3000, 0.50, '2025-12-15', '2025-07-01', 3000),
('106-20-B0006', 106, 20, 600, 0.50, '2025-12-20', '2025-07-01', 600),
('108-20-B0001', 108, 20, 1000, 0.25, '2025-09-28', '2025-06-30', 1000),
('108-20-B0003', 108, 20, 6300, 0.25, '2025-12-31', '2025-07-01', 6300),
('201-20-B0001', 201, 20, 100, 2.50, '2025-11-30', '2025-07-01', 100),
('201-20-B0002', 201, 20, 20, 2.50, '2025-12-30', '2025-07-01', 20);


-- ===========================================================
-- PRODUCT BATCHES
-- ===========================================================
INSERT INTO ProductBatch (lot_number, product_id, manufacturer_id, recipe_id, produced_qty, produced_at, expiration_date, total_batch_cost, per_unit_cost)
VALUES
('100-MFG001-B0901', 100, 'MFG001', 1, 100, '2025-09-26', '2025-11-15', 1000.00, 10.00),
('101-MFG002-B0101', 101, 'MFG002', 2, 300, '2025-09-10', '2025-10-30', 1500.00, 5.00);

-- ===========================================================
-- PRODUCTION CONSUMPTION
-- ===========================================================
INSERT INTO ProductionConsumption (product_batch, ingredient_lot, qty)
VALUES
('100-MFG001-B0901', '106-20-B0006', 600),
('100-MFG001-B0901', '201-20-B0002', 20),
('101-MFG002-B0101', '101-20-B0002', 150),
('101-MFG002-B0101', '108-20-B0003', 2100),
('101-MFG002-B0101', '102-20-B0001', 600);

-- ===========================================================
-- CONFLICT PAIRS
-- ===========================================================
INSERT INTO ConflictPairs (ingredient_a, ingredient_b, reason, severity)
VALUES
(106, 104, 'Cannot combine Sodium Phosphate with Beef Steak', 'CRITICAL');

SELECT '✅ Sample data loaded successfully!' AS status;
