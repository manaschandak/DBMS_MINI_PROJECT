--
-- PostgreSQL database dump
--

\restrict 37kgtAXZdEU389YfGUdmd2IvLe5XzimGApT8acnfwHJEH2f4uGoEwQVAzcO3P5c

-- Dumped from database version 18.6
-- Dumped by pg_dump version 18.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: fn_create_alert_for_risk(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.fn_create_alert_for_risk() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_serial       TEXT;
    v_risk_type    TEXT;
    v_priority_id  INTEGER;
BEGIN
    -- Only HIGH and CRITICAL raise an alert; LOW and MEDIUM do not.
    IF NEW.final_risk_level IN ('HIGH', 'CRITICAL') THEN

        SELECT b.serial_number, m.risk_type
          INTO v_serial, v_risk_type
          FROM prediction_result pr
          JOIN battery b  ON pr.battery_id = b.battery_id
          JOIN ai_model m ON pr.model_id = m.model_id
         WHERE pr.prediction_id = NEW.prediction_id;

        -- priority_code in alert_priority matches the risk level name (HIGH, CRITICAL)
        SELECT alert_priority_id
          INTO v_priority_id
          FROM alert_priority
         WHERE priority_code = NEW.final_risk_level;

        INSERT INTO alert (assessment_id, alert_priority_id, message, status)
        VALUES (
            NEW.assessment_id,
            v_priority_id,
            format('AUTO: %s %s risk on %s',
                   NEW.final_risk_level, lower(v_risk_type), v_serial),
            'OPEN'
        );
    END IF;

    RETURN NEW;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: aging_record; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.aging_record (
    aging_id integer NOT NULL,
    battery_id integer NOT NULL,
    measured_at timestamp with time zone NOT NULL,
    cycle_count integer NOT NULL,
    calendar_age_days integer NOT NULL,
    capacity_ah numeric(8,2) NOT NULL,
    internal_resistance_mohm numeric(8,3) NOT NULL,
    data_source_id integer NOT NULL,
    CONSTRAINT aging_record_calendar_age_days_check CHECK ((calendar_age_days >= 0)),
    CONSTRAINT aging_record_capacity_ah_check CHECK ((capacity_ah > (0)::numeric)),
    CONSTRAINT aging_record_cycle_count_check CHECK ((cycle_count >= 0)),
    CONSTRAINT aging_record_internal_resistance_mohm_check CHECK ((internal_resistance_mohm > (0)::numeric))
);


--
-- Name: aging_record_aging_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.aging_record ALTER COLUMN aging_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.aging_record_aging_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: ai_model; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_model (
    model_id integer NOT NULL,
    model_name character varying(100) NOT NULL,
    version character varying(20) NOT NULL,
    task_type character varying(30) NOT NULL,
    algorithm character varying(50) NOT NULL,
    trained_at timestamp with time zone,
    artifact_path character varying(255),
    is_active boolean DEFAULT false NOT NULL,
    notes text,
    risk_type character varying(10),
    CONSTRAINT ai_model_risk_type_check CHECK (((risk_type)::text = ANY ((ARRAY['THERMAL'::character varying, 'HEALTH'::character varying])::text[]))),
    CONSTRAINT ai_model_task_type_check CHECK (((task_type)::text = ANY ((ARRAY['RISK_CLASSIFICATION'::character varying, 'ANOMALY_DETECTION'::character varying, 'DEGRADATION_REGRESSION'::character varying])::text[]))),
    CONSTRAINT chk_classifier_has_risk_type CHECK ((((task_type)::text <> 'RISK_CLASSIFICATION'::text) OR (risk_type IS NOT NULL)))
);


--
-- Name: ai_model_model_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.ai_model ALTER COLUMN model_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.ai_model_model_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: alert; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alert (
    alert_id integer NOT NULL,
    assessment_id integer NOT NULL,
    alert_priority_id integer NOT NULL,
    message text NOT NULL,
    status character varying(15) DEFAULT 'OPEN'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    acknowledged_at timestamp with time zone,
    CONSTRAINT alert_status_check CHECK (((status)::text = ANY ((ARRAY['OPEN'::character varying, 'ACKNOWLEDGED'::character varying, 'RESOLVED'::character varying])::text[]))),
    CONSTRAINT chk_alert_ack_matches_status CHECK (((((status)::text = 'OPEN'::text) AND (acknowledged_at IS NULL)) OR (((status)::text <> 'OPEN'::text) AND (acknowledged_at IS NOT NULL))))
);


--
-- Name: alert_alert_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.alert ALTER COLUMN alert_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.alert_alert_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: alert_priority; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alert_priority (
    alert_priority_id integer NOT NULL,
    priority_code character varying(10) NOT NULL,
    severity_level integer NOT NULL,
    description text,
    CONSTRAINT alert_priority_severity_level_check CHECK (((severity_level >= 1) AND (severity_level <= 4)))
);


--
-- Name: alert_priority_alert_priority_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.alert_priority ALTER COLUMN alert_priority_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.alert_priority_alert_priority_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: app_user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.app_user (
    user_id integer NOT NULL,
    username character varying(50) NOT NULL,
    full_name character varying(100) NOT NULL,
    email character varying(150) NOT NULL,
    password_hash text NOT NULL,
    role character varying(20) NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    last_login_at timestamp with time zone,
    CONSTRAINT app_user_password_hash_check CHECK ((length(password_hash) >= 20)),
    CONSTRAINT app_user_role_check CHECK (((role)::text = ANY ((ARRAY['ADMIN'::character varying, 'BMS_ENGINEER'::character varying, 'FLEET_OPERATOR'::character varying, 'SERVICE_TECHNICIAN'::character varying, 'RESEARCHER'::character varying])::text[])))
);


--
-- Name: app_user_user_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.app_user ALTER COLUMN user_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.app_user_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: battery; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.battery (
    battery_id integer NOT NULL,
    serial_number character varying(50) NOT NULL,
    battery_type character varying(10) DEFAULT 'PACK'::character varying NOT NULL,
    manufacturer_id integer NOT NULL,
    chemistry_id integer NOT NULL,
    nominal_capacity_ah numeric(8,2) NOT NULL,
    install_date date,
    status character varying(20) DEFAULT 'ACTIVE'::character varying NOT NULL,
    CONSTRAINT battery_battery_type_check CHECK (((battery_type)::text = ANY ((ARRAY['PACK'::character varying, 'CELL'::character varying])::text[]))),
    CONSTRAINT battery_nominal_capacity_ah_check CHECK ((nominal_capacity_ah > (0)::numeric)),
    CONSTRAINT battery_status_check CHECK (((status)::text = ANY ((ARRAY['ACTIVE'::character varying, 'MAINTENANCE'::character varying, 'RETIRED'::character varying])::text[])))
);


--
-- Name: battery_battery_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.battery ALTER COLUMN battery_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.battery_battery_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: cfd_simulation; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cfd_simulation (
    simulation_id integer NOT NULL,
    twin_id integer NOT NULL,
    run_at timestamp with time zone DEFAULT now() NOT NULL,
    flow_rate_lpm numeric(6,2) NOT NULL,
    inlet_temp_c numeric(5,2) NOT NULL,
    max_temp_c numeric(5,2) NOT NULL,
    avg_temp_c numeric(5,2) NOT NULL,
    pressure_drop_kpa numeric(7,2),
    data_source_id integer NOT NULL,
    CONSTRAINT cfd_simulation_flow_rate_lpm_check CHECK ((flow_rate_lpm > (0)::numeric)),
    CONSTRAINT cfd_simulation_pressure_drop_kpa_check CHECK ((pressure_drop_kpa >= (0)::numeric)),
    CONSTRAINT chk_cfd_max_ge_avg CHECK ((max_temp_c >= avg_temp_c))
);


--
-- Name: cfd_simulation_simulation_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.cfd_simulation ALTER COLUMN simulation_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.cfd_simulation_simulation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: chemistry; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chemistry (
    chemistry_id integer NOT NULL,
    chemistry_code character varying(10) NOT NULL,
    chemistry_name character varying(100) NOT NULL
);


--
-- Name: chemistry_chemistry_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.chemistry ALTER COLUMN chemistry_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.chemistry_chemistry_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: coolant_flow; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.coolant_flow (
    sensor_id integer NOT NULL,
    recorded_at timestamp with time zone NOT NULL,
    flow_rate_lpm numeric(6,2) NOT NULL,
    inlet_temp_c numeric(5,2),
    data_source_id integer NOT NULL,
    CONSTRAINT coolant_flow_flow_rate_lpm_check CHECK ((flow_rate_lpm >= (0)::numeric))
);


--
-- Name: data_source; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.data_source (
    data_source_id integer NOT NULL,
    source_name character varying(100) NOT NULL,
    source_type character varying(20) NOT NULL,
    description text,
    CONSTRAINT data_source_source_type_check CHECK (((source_type)::text = ANY ((ARRAY['SIMULATOR'::character varying, 'CSV_UPLOAD'::character varying, 'MANUAL_ENTRY'::character varying, 'CFD_IMPORT'::character varying, 'PUBLIC_DATASET'::character varying, 'SENSOR_HARDWARE'::character varying])::text[])))
);


--
-- Name: data_source_data_source_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.data_source ALTER COLUMN data_source_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.data_source_data_source_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: digital_twin; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.digital_twin (
    twin_id integer NOT NULL,
    battery_id integer NOT NULL,
    model_version character varying(30) NOT NULL,
    last_synced_at timestamp with time zone,
    simulated_soh_pct numeric(5,2),
    CONSTRAINT digital_twin_simulated_soh_pct_check CHECK (((simulated_soh_pct >= (0)::numeric) AND (simulated_soh_pct <= (100)::numeric)))
);


--
-- Name: digital_twin_twin_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.digital_twin ALTER COLUMN twin_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.digital_twin_twin_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: electrical_reading; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.electrical_reading (
    sensor_id integer NOT NULL,
    recorded_at timestamp with time zone NOT NULL,
    voltage_v numeric(6,3) NOT NULL,
    current_a numeric(8,3) NOT NULL,
    data_source_id integer NOT NULL,
    CONSTRAINT electrical_reading_voltage_v_check CHECK (((voltage_v >= (0)::numeric) AND (voltage_v <= (1000)::numeric)))
);


--
-- Name: feedback; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.feedback (
    feedback_id integer NOT NULL,
    prediction_id integer NOT NULL,
    actual_outcome character varying(10) NOT NULL,
    outcome_source character varying(20) NOT NULL,
    submitted_by_role character varying(20) NOT NULL,
    observed_at timestamp with time zone DEFAULT now() NOT NULL,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT feedback_actual_outcome_check CHECK (((actual_outcome)::text = ANY ((ARRAY['LOW'::character varying, 'MEDIUM'::character varying, 'HIGH'::character varying, 'CRITICAL'::character varying])::text[]))),
    CONSTRAINT feedback_outcome_source_check CHECK (((outcome_source)::text = ANY ((ARRAY['SERVICE_INSPECTION'::character varying, 'LAB_TEST'::character varying, 'FIELD_OBSERVATION'::character varying, 'SIMULATION'::character varying])::text[]))),
    CONSTRAINT feedback_submitted_by_role_check CHECK (((submitted_by_role)::text = ANY ((ARRAY['ADMIN'::character varying, 'BMS_ENGINEER'::character varying, 'FLEET_OPERATOR'::character varying, 'SERVICE_TECHNICIAN'::character varying, 'RESEARCHER'::character varying])::text[])))
);


--
-- Name: feedback_feedback_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.feedback ALTER COLUMN feedback_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.feedback_feedback_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: manufacturer; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.manufacturer (
    manufacturer_id integer NOT NULL,
    manufacturer_name character varying(100) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: manufacturer_manufacturer_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.manufacturer ALTER COLUMN manufacturer_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.manufacturer_manufacturer_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: model_performance; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.model_performance (
    performance_id integer NOT NULL,
    model_id integer NOT NULL,
    evaluation_type character varying(15) NOT NULL,
    sample_count integer NOT NULL,
    accuracy numeric(4,3),
    macro_f1 numeric(4,3),
    recall_high_critical numeric(4,3),
    evaluated_at timestamp with time zone DEFAULT now() NOT NULL,
    notes text,
    CONSTRAINT model_performance_accuracy_check CHECK (((accuracy >= (0)::numeric) AND (accuracy <= (1)::numeric))),
    CONSTRAINT model_performance_evaluation_type_check CHECK (((evaluation_type)::text = ANY ((ARRAY['TEST_SET'::character varying, 'LIVE_FEEDBACK'::character varying])::text[]))),
    CONSTRAINT model_performance_macro_f1_check CHECK (((macro_f1 >= (0)::numeric) AND (macro_f1 <= (1)::numeric))),
    CONSTRAINT model_performance_recall_high_critical_check CHECK (((recall_high_critical >= (0)::numeric) AND (recall_high_critical <= (1)::numeric))),
    CONSTRAINT model_performance_sample_count_check CHECK ((sample_count > 0))
);


--
-- Name: model_performance_performance_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.model_performance ALTER COLUMN performance_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.model_performance_performance_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: model_training; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.model_training (
    model_id integer NOT NULL,
    dataset_id integer NOT NULL,
    rows_used integer,
    CONSTRAINT model_training_rows_used_check CHECK ((rows_used >= 0))
);


--
-- Name: prediction_result; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.prediction_result (
    prediction_id integer NOT NULL,
    model_id integer NOT NULL,
    battery_id integer NOT NULL,
    predicted_at timestamp with time zone DEFAULT now() NOT NULL,
    predicted_label character varying(10) NOT NULL,
    confidence numeric(4,3),
    notes text,
    CONSTRAINT prediction_result_confidence_check CHECK (((confidence >= (0)::numeric) AND (confidence <= (1)::numeric))),
    CONSTRAINT prediction_result_predicted_label_check CHECK (((predicted_label)::text = ANY ((ARRAY['LOW'::character varying, 'MEDIUM'::character varying, 'HIGH'::character varying, 'CRITICAL'::character varying])::text[])))
);


--
-- Name: prediction_result_prediction_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.prediction_result ALTER COLUMN prediction_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.prediction_result_prediction_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: recommendation; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.recommendation (
    recommendation_id integer NOT NULL,
    target_role character varying(20) NOT NULL,
    assessment_id integer,
    anomaly_id integer,
    recommendation_text text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_recommendation_one_source CHECK ((num_nonnulls(assessment_id, anomaly_id) = 1)),
    CONSTRAINT recommendation_target_role_check CHECK (((target_role)::text = ANY ((ARRAY['BMS_ENGINEER'::character varying, 'FLEET_OPERATOR'::character varying, 'MANUFACTURER'::character varying, 'SERVICE_TECHNICIAN'::character varying])::text[])))
);


--
-- Name: recommendation_recommendation_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.recommendation ALTER COLUMN recommendation_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.recommendation_recommendation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: risk_assessment; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.risk_assessment (
    assessment_id integer NOT NULL,
    prediction_id integer NOT NULL,
    final_risk_level character varying(10) NOT NULL,
    rule_override boolean DEFAULT false NOT NULL,
    assessed_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT risk_assessment_final_risk_level_check CHECK (((final_risk_level)::text = ANY ((ARRAY['LOW'::character varying, 'MEDIUM'::character varying, 'HIGH'::character varying, 'CRITICAL'::character varying])::text[])))
);


--
-- Name: risk_assessment_assessment_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.risk_assessment ALTER COLUMN assessment_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.risk_assessment_assessment_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: sensor; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sensor (
    sensor_id integer NOT NULL,
    battery_id integer NOT NULL,
    sensor_type character varying(20) NOT NULL,
    location character varying(50) NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    CONSTRAINT sensor_sensor_type_check CHECK (((sensor_type)::text = ANY ((ARRAY['TEMPERATURE'::character varying, 'COOLANT_FLOW'::character varying, 'ELECTRICAL'::character varying])::text[])))
);


--
-- Name: sensor_anomaly; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sensor_anomaly (
    anomaly_id integer NOT NULL,
    sensor_id integer NOT NULL,
    detected_at timestamp with time zone NOT NULL,
    anomaly_type character varying(20) NOT NULL,
    cause character varying(15) DEFAULT 'UNDETERMINED'::character varying NOT NULL,
    detection_method character varying(10) NOT NULL,
    model_id integer,
    anomaly_score numeric(6,3),
    details text,
    CONSTRAINT chk_anomaly_method_matches_model CHECK ((((detection_method)::text = 'ML_MODEL'::text) = (model_id IS NOT NULL))),
    CONSTRAINT sensor_anomaly_anomaly_type_check CHECK (((anomaly_type)::text = ANY ((ARRAY['OUT_OF_RANGE'::character varying, 'SUDDEN_SPIKE'::character varying, 'FLATLINE'::character varying, 'DRIFT'::character varying, 'MODEL_OUTLIER'::character varying])::text[]))),
    CONSTRAINT sensor_anomaly_cause_check CHECK (((cause)::text = ANY ((ARRAY['SENSOR_FAULT'::character varying, 'BATTERY_ISSUE'::character varying, 'UNDETERMINED'::character varying])::text[]))),
    CONSTRAINT sensor_anomaly_detection_method_check CHECK (((detection_method)::text = ANY ((ARRAY['RULE'::character varying, 'ML_MODEL'::character varying])::text[])))
);


--
-- Name: sensor_anomaly_anomaly_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.sensor_anomaly ALTER COLUMN anomaly_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.sensor_anomaly_anomaly_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: sensor_sensor_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.sensor ALTER COLUMN sensor_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.sensor_sensor_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: temperature_reading; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.temperature_reading (
    sensor_id integer NOT NULL,
    recorded_at timestamp with time zone NOT NULL,
    temperature_c numeric(5,2) NOT NULL,
    data_source_id integer NOT NULL,
    CONSTRAINT temperature_reading_temperature_c_check CHECK (((temperature_c >= ('-50'::integer)::numeric) AND (temperature_c <= (200)::numeric)))
);


--
-- Name: training_dataset; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.training_dataset (
    dataset_id integer NOT NULL,
    dataset_name character varying(100) NOT NULL,
    version character varying(20) NOT NULL,
    data_source_id integer NOT NULL,
    is_synthetic boolean DEFAULT true NOT NULL,
    row_count integer,
    file_path character varying(255),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    notes text,
    CONSTRAINT training_dataset_row_count_check CHECK ((row_count >= 0))
);


--
-- Name: training_dataset_dataset_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.training_dataset ALTER COLUMN dataset_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.training_dataset_dataset_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: v_latest_risk; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_latest_risk AS
 SELECT DISTINCT ON (pr.battery_id, m.risk_type) pr.battery_id,
    m.risk_type,
    ra.final_risk_level,
    ra.rule_override,
    ra.assessed_at
   FROM ((public.risk_assessment ra
     JOIN public.prediction_result pr ON ((ra.prediction_id = pr.prediction_id)))
     JOIN public.ai_model m ON ((pr.model_id = m.model_id)))
  ORDER BY pr.battery_id, m.risk_type, ra.assessed_at DESC;


--
-- Name: v_battery_overview; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_battery_overview AS
 SELECT b.battery_id,
    b.serial_number,
    mf.manufacturer_name,
    c.chemistry_code,
    b.status,
    ( SELECT max(lt.temperature_c) AS max
           FROM (public.sensor s
             CROSS JOIN LATERAL ( SELECT tr.temperature_c
                   FROM public.temperature_reading tr
                  WHERE (tr.sensor_id = s.sensor_id)
                  ORDER BY tr.recorded_at DESC
                 LIMIT 1) lt)
          WHERE (s.battery_id = b.battery_id)) AS latest_max_temp_c,
    lt_risk.final_risk_level AS thermal_risk,
    lh_risk.final_risk_level AS health_risk,
    ( SELECT count(*) AS count
           FROM ((public.alert a
             JOIN public.risk_assessment ra ON ((a.assessment_id = ra.assessment_id)))
             JOIN public.prediction_result pr ON ((ra.prediction_id = pr.prediction_id)))
          WHERE ((pr.battery_id = b.battery_id) AND ((a.status)::text = 'OPEN'::text))) AS open_alerts
   FROM ((((public.battery b
     JOIN public.manufacturer mf ON ((b.manufacturer_id = mf.manufacturer_id)))
     JOIN public.chemistry c ON ((b.chemistry_id = c.chemistry_id)))
     LEFT JOIN public.v_latest_risk lt_risk ON (((lt_risk.battery_id = b.battery_id) AND ((lt_risk.risk_type)::text = 'THERMAL'::text))))
     LEFT JOIN public.v_latest_risk lh_risk ON (((lh_risk.battery_id = b.battery_id) AND ((lh_risk.risk_type)::text = 'HEALTH'::text))));


--
-- Name: v_chemistry_comparison; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_chemistry_comparison AS
 WITH latest_aging AS (
         SELECT DISTINCT ON (aging_record.battery_id) aging_record.battery_id,
            aging_record.cycle_count,
            aging_record.internal_resistance_mohm,
            aging_record.capacity_ah
           FROM public.aging_record
          ORDER BY aging_record.battery_id, aging_record.measured_at DESC
        ), peak_temp AS (
         SELECT s.battery_id,
            max(tr.temperature_c) AS peak_temp_c
           FROM (public.temperature_reading tr
             JOIN public.sensor s ON ((tr.sensor_id = s.sensor_id)))
          GROUP BY s.battery_id
        )
 SELECT c.chemistry_code,
    c.chemistry_name,
    count(DISTINCT b.battery_id) AS battery_count,
    round(avg(la.cycle_count), 0) AS avg_cycles,
    round(avg(la.internal_resistance_mohm), 2) AS avg_resistance_mohm,
    round(avg(((la.capacity_ah / b.nominal_capacity_ah) * (100)::numeric)), 1) AS avg_capacity_pct_of_nominal,
    round(avg(pt.peak_temp_c), 1) AS avg_peak_temp_c,
    max(pt.peak_temp_c) AS max_peak_temp_c
   FROM (((public.chemistry c
     LEFT JOIN public.battery b ON ((b.chemistry_id = c.chemistry_id)))
     LEFT JOIN latest_aging la ON ((la.battery_id = b.battery_id)))
     LEFT JOIN peak_temp pt ON ((pt.battery_id = b.battery_id)))
  GROUP BY c.chemistry_code, c.chemistry_name;


--
-- Name: v_live_accuracy; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_live_accuracy AS
 SELECT m.model_id,
    m.model_name,
    m.risk_type,
    count(*) AS feedback_count,
    count(*) FILTER (WHERE ((p.predicted_label)::text = (f.actual_outcome)::text)) AS exact_matches,
    round(((count(*) FILTER (WHERE ((p.predicted_label)::text = (f.actual_outcome)::text)))::numeric / (count(*))::numeric), 3) AS accuracy,
    count(*) FILTER (WHERE (array_position(ARRAY['LOW'::text, 'MEDIUM'::text, 'HIGH'::text, 'CRITICAL'::text], (f.actual_outcome)::text) > array_position(ARRAY['LOW'::text, 'MEDIUM'::text, 'HIGH'::text, 'CRITICAL'::text], (p.predicted_label)::text))) AS underestimated
   FROM ((public.feedback f
     JOIN public.prediction_result p ON ((f.prediction_id = p.prediction_id)))
     JOIN public.ai_model m ON ((p.model_id = m.model_id)))
  GROUP BY m.model_id, m.model_name, m.risk_type;


--
-- Name: v_open_alerts; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_open_alerts AS
 SELECT a.alert_id,
    ap.priority_code,
    ap.severity_level,
    b.serial_number,
    ra.final_risk_level,
    a.message,
    a.status,
    a.created_at
   FROM ((((public.alert a
     JOIN public.alert_priority ap ON ((a.alert_priority_id = ap.alert_priority_id)))
     JOIN public.risk_assessment ra ON ((a.assessment_id = ra.assessment_id)))
     JOIN public.prediction_result pr ON ((ra.prediction_id = pr.prediction_id)))
     JOIN public.battery b ON ((pr.battery_id = b.battery_id)))
  WHERE ((a.status)::text = 'OPEN'::text);


--
-- Name: v_risk_distribution; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_risk_distribution AS
 SELECT risk_type,
    final_risk_level,
    count(*) AS battery_count
   FROM public.v_latest_risk
  GROUP BY risk_type, final_risk_level;


--
-- Name: aging_record aging_record_battery_id_measured_at_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.aging_record
    ADD CONSTRAINT aging_record_battery_id_measured_at_key UNIQUE (battery_id, measured_at);


--
-- Name: aging_record aging_record_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.aging_record
    ADD CONSTRAINT aging_record_pkey PRIMARY KEY (aging_id);


--
-- Name: ai_model ai_model_model_name_version_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_model
    ADD CONSTRAINT ai_model_model_name_version_key UNIQUE (model_name, version);


--
-- Name: ai_model ai_model_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_model
    ADD CONSTRAINT ai_model_pkey PRIMARY KEY (model_id);


--
-- Name: alert alert_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert
    ADD CONSTRAINT alert_pkey PRIMARY KEY (alert_id);


--
-- Name: alert_priority alert_priority_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert_priority
    ADD CONSTRAINT alert_priority_pkey PRIMARY KEY (alert_priority_id);


--
-- Name: alert_priority alert_priority_priority_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert_priority
    ADD CONSTRAINT alert_priority_priority_code_key UNIQUE (priority_code);


--
-- Name: alert_priority alert_priority_severity_level_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert_priority
    ADD CONSTRAINT alert_priority_severity_level_key UNIQUE (severity_level);


--
-- Name: app_user app_user_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_user
    ADD CONSTRAINT app_user_email_key UNIQUE (email);


--
-- Name: app_user app_user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_user
    ADD CONSTRAINT app_user_pkey PRIMARY KEY (user_id);


--
-- Name: app_user app_user_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_user
    ADD CONSTRAINT app_user_username_key UNIQUE (username);


--
-- Name: battery battery_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.battery
    ADD CONSTRAINT battery_pkey PRIMARY KEY (battery_id);


--
-- Name: battery battery_serial_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.battery
    ADD CONSTRAINT battery_serial_number_key UNIQUE (serial_number);


--
-- Name: cfd_simulation cfd_simulation_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cfd_simulation
    ADD CONSTRAINT cfd_simulation_pkey PRIMARY KEY (simulation_id);


--
-- Name: chemistry chemistry_chemistry_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chemistry
    ADD CONSTRAINT chemistry_chemistry_code_key UNIQUE (chemistry_code);


--
-- Name: chemistry chemistry_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chemistry
    ADD CONSTRAINT chemistry_pkey PRIMARY KEY (chemistry_id);


--
-- Name: coolant_flow coolant_flow_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.coolant_flow
    ADD CONSTRAINT coolant_flow_pkey PRIMARY KEY (sensor_id, recorded_at);


--
-- Name: data_source data_source_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_source
    ADD CONSTRAINT data_source_pkey PRIMARY KEY (data_source_id);


--
-- Name: data_source data_source_source_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_source
    ADD CONSTRAINT data_source_source_name_key UNIQUE (source_name);


--
-- Name: digital_twin digital_twin_battery_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.digital_twin
    ADD CONSTRAINT digital_twin_battery_id_key UNIQUE (battery_id);


--
-- Name: digital_twin digital_twin_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.digital_twin
    ADD CONSTRAINT digital_twin_pkey PRIMARY KEY (twin_id);


--
-- Name: electrical_reading electrical_reading_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.electrical_reading
    ADD CONSTRAINT electrical_reading_pkey PRIMARY KEY (sensor_id, recorded_at);


--
-- Name: feedback feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT feedback_pkey PRIMARY KEY (feedback_id);


--
-- Name: manufacturer manufacturer_manufacturer_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.manufacturer
    ADD CONSTRAINT manufacturer_manufacturer_name_key UNIQUE (manufacturer_name);


--
-- Name: manufacturer manufacturer_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.manufacturer
    ADD CONSTRAINT manufacturer_pkey PRIMARY KEY (manufacturer_id);


--
-- Name: model_performance model_performance_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_performance
    ADD CONSTRAINT model_performance_pkey PRIMARY KEY (performance_id);


--
-- Name: model_training model_training_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_training
    ADD CONSTRAINT model_training_pkey PRIMARY KEY (model_id, dataset_id);


--
-- Name: prediction_result prediction_result_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prediction_result
    ADD CONSTRAINT prediction_result_pkey PRIMARY KEY (prediction_id);


--
-- Name: recommendation recommendation_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recommendation
    ADD CONSTRAINT recommendation_pkey PRIMARY KEY (recommendation_id);


--
-- Name: risk_assessment risk_assessment_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.risk_assessment
    ADD CONSTRAINT risk_assessment_pkey PRIMARY KEY (assessment_id);


--
-- Name: risk_assessment risk_assessment_prediction_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.risk_assessment
    ADD CONSTRAINT risk_assessment_prediction_id_key UNIQUE (prediction_id);


--
-- Name: sensor_anomaly sensor_anomaly_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor_anomaly
    ADD CONSTRAINT sensor_anomaly_pkey PRIMARY KEY (anomaly_id);


--
-- Name: sensor_anomaly sensor_anomaly_sensor_id_detected_at_anomaly_type_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor_anomaly
    ADD CONSTRAINT sensor_anomaly_sensor_id_detected_at_anomaly_type_key UNIQUE (sensor_id, detected_at, anomaly_type);


--
-- Name: sensor sensor_battery_id_location_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor
    ADD CONSTRAINT sensor_battery_id_location_key UNIQUE (battery_id, location);


--
-- Name: sensor sensor_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor
    ADD CONSTRAINT sensor_pkey PRIMARY KEY (sensor_id);


--
-- Name: temperature_reading temperature_reading_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.temperature_reading
    ADD CONSTRAINT temperature_reading_pkey PRIMARY KEY (sensor_id, recorded_at);


--
-- Name: training_dataset training_dataset_dataset_name_version_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_dataset
    ADD CONSTRAINT training_dataset_dataset_name_version_key UNIQUE (dataset_name, version);


--
-- Name: training_dataset training_dataset_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_dataset
    ADD CONSTRAINT training_dataset_pkey PRIMARY KEY (dataset_id);


--
-- Name: idx_alert_assessment; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alert_assessment ON public.alert USING btree (assessment_id);


--
-- Name: idx_alert_open; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alert_open ON public.alert USING btree (alert_priority_id, created_at DESC) WHERE ((status)::text = 'OPEN'::text);


--
-- Name: idx_anomaly_detected_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_anomaly_detected_at ON public.sensor_anomaly USING btree (detected_at DESC);


--
-- Name: idx_battery_chemistry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_battery_chemistry ON public.battery USING btree (chemistry_id);


--
-- Name: idx_battery_manufacturer; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_battery_manufacturer ON public.battery USING btree (manufacturer_id);


--
-- Name: idx_cfd_twin_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cfd_twin_time ON public.cfd_simulation USING btree (twin_id, run_at DESC);


--
-- Name: idx_feedback_prediction; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_feedback_prediction ON public.feedback USING btree (prediction_id);


--
-- Name: idx_model_performance_model; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_model_performance_model ON public.model_performance USING btree (model_id, evaluated_at);


--
-- Name: idx_model_training_dataset; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_model_training_dataset ON public.model_training USING btree (dataset_id);


--
-- Name: idx_prediction_battery_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prediction_battery_time ON public.prediction_result USING btree (battery_id, predicted_at DESC);


--
-- Name: idx_prediction_model; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prediction_model ON public.prediction_result USING btree (model_id);


--
-- Name: idx_recommendation_anomaly; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recommendation_anomaly ON public.recommendation USING btree (anomaly_id);


--
-- Name: idx_recommendation_assessment; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recommendation_assessment ON public.recommendation USING btree (assessment_id);


--
-- Name: idx_recommendation_role_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recommendation_role_time ON public.recommendation USING btree (target_role, created_at DESC);


--
-- Name: idx_temperature_time_brin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_temperature_time_brin ON public.temperature_reading USING brin (recorded_at);


--
-- Name: idx_temperature_value; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_temperature_value ON public.temperature_reading USING btree (temperature_c);


--
-- Name: risk_assessment trg_alert_on_risk; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_alert_on_risk AFTER INSERT ON public.risk_assessment FOR EACH ROW EXECUTE FUNCTION public.fn_create_alert_for_risk();


--
-- Name: aging_record aging_record_battery_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.aging_record
    ADD CONSTRAINT aging_record_battery_id_fkey FOREIGN KEY (battery_id) REFERENCES public.battery(battery_id);


--
-- Name: aging_record aging_record_data_source_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.aging_record
    ADD CONSTRAINT aging_record_data_source_id_fkey FOREIGN KEY (data_source_id) REFERENCES public.data_source(data_source_id);


--
-- Name: alert alert_alert_priority_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert
    ADD CONSTRAINT alert_alert_priority_id_fkey FOREIGN KEY (alert_priority_id) REFERENCES public.alert_priority(alert_priority_id);


--
-- Name: alert alert_assessment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert
    ADD CONSTRAINT alert_assessment_id_fkey FOREIGN KEY (assessment_id) REFERENCES public.risk_assessment(assessment_id);


--
-- Name: battery battery_chemistry_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.battery
    ADD CONSTRAINT battery_chemistry_id_fkey FOREIGN KEY (chemistry_id) REFERENCES public.chemistry(chemistry_id);


--
-- Name: battery battery_manufacturer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.battery
    ADD CONSTRAINT battery_manufacturer_id_fkey FOREIGN KEY (manufacturer_id) REFERENCES public.manufacturer(manufacturer_id);


--
-- Name: cfd_simulation cfd_simulation_data_source_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cfd_simulation
    ADD CONSTRAINT cfd_simulation_data_source_id_fkey FOREIGN KEY (data_source_id) REFERENCES public.data_source(data_source_id);


--
-- Name: cfd_simulation cfd_simulation_twin_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cfd_simulation
    ADD CONSTRAINT cfd_simulation_twin_id_fkey FOREIGN KEY (twin_id) REFERENCES public.digital_twin(twin_id);


--
-- Name: coolant_flow coolant_flow_data_source_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.coolant_flow
    ADD CONSTRAINT coolant_flow_data_source_id_fkey FOREIGN KEY (data_source_id) REFERENCES public.data_source(data_source_id);


--
-- Name: coolant_flow coolant_flow_sensor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.coolant_flow
    ADD CONSTRAINT coolant_flow_sensor_id_fkey FOREIGN KEY (sensor_id) REFERENCES public.sensor(sensor_id);


--
-- Name: digital_twin digital_twin_battery_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.digital_twin
    ADD CONSTRAINT digital_twin_battery_id_fkey FOREIGN KEY (battery_id) REFERENCES public.battery(battery_id);


--
-- Name: electrical_reading electrical_reading_data_source_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.electrical_reading
    ADD CONSTRAINT electrical_reading_data_source_id_fkey FOREIGN KEY (data_source_id) REFERENCES public.data_source(data_source_id);


--
-- Name: electrical_reading electrical_reading_sensor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.electrical_reading
    ADD CONSTRAINT electrical_reading_sensor_id_fkey FOREIGN KEY (sensor_id) REFERENCES public.sensor(sensor_id);


--
-- Name: feedback feedback_prediction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT feedback_prediction_id_fkey FOREIGN KEY (prediction_id) REFERENCES public.prediction_result(prediction_id) ON DELETE CASCADE;


--
-- Name: model_performance model_performance_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_performance
    ADD CONSTRAINT model_performance_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.ai_model(model_id) ON DELETE CASCADE;


--
-- Name: model_training model_training_dataset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_training
    ADD CONSTRAINT model_training_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES public.training_dataset(dataset_id);


--
-- Name: model_training model_training_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_training
    ADD CONSTRAINT model_training_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.ai_model(model_id);


--
-- Name: prediction_result prediction_result_battery_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prediction_result
    ADD CONSTRAINT prediction_result_battery_id_fkey FOREIGN KEY (battery_id) REFERENCES public.battery(battery_id);


--
-- Name: prediction_result prediction_result_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prediction_result
    ADD CONSTRAINT prediction_result_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.ai_model(model_id);


--
-- Name: recommendation recommendation_anomaly_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recommendation
    ADD CONSTRAINT recommendation_anomaly_id_fkey FOREIGN KEY (anomaly_id) REFERENCES public.sensor_anomaly(anomaly_id);


--
-- Name: recommendation recommendation_assessment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recommendation
    ADD CONSTRAINT recommendation_assessment_id_fkey FOREIGN KEY (assessment_id) REFERENCES public.risk_assessment(assessment_id);


--
-- Name: risk_assessment risk_assessment_prediction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.risk_assessment
    ADD CONSTRAINT risk_assessment_prediction_id_fkey FOREIGN KEY (prediction_id) REFERENCES public.prediction_result(prediction_id);


--
-- Name: sensor_anomaly sensor_anomaly_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor_anomaly
    ADD CONSTRAINT sensor_anomaly_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.ai_model(model_id);


--
-- Name: sensor_anomaly sensor_anomaly_sensor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor_anomaly
    ADD CONSTRAINT sensor_anomaly_sensor_id_fkey FOREIGN KEY (sensor_id) REFERENCES public.sensor(sensor_id);


--
-- Name: sensor sensor_battery_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor
    ADD CONSTRAINT sensor_battery_id_fkey FOREIGN KEY (battery_id) REFERENCES public.battery(battery_id);


--
-- Name: temperature_reading temperature_reading_data_source_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.temperature_reading
    ADD CONSTRAINT temperature_reading_data_source_id_fkey FOREIGN KEY (data_source_id) REFERENCES public.data_source(data_source_id);


--
-- Name: temperature_reading temperature_reading_sensor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.temperature_reading
    ADD CONSTRAINT temperature_reading_sensor_id_fkey FOREIGN KEY (sensor_id) REFERENCES public.sensor(sensor_id);


--
-- Name: training_dataset training_dataset_data_source_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_dataset
    ADD CONSTRAINT training_dataset_data_source_id_fkey FOREIGN KEY (data_source_id) REFERENCES public.data_source(data_source_id);


--
-- PostgreSQL database dump complete
--

\unrestrict 37kgtAXZdEU389YfGUdmd2IvLe5XzimGApT8acnfwHJEH2f4uGoEwQVAzcO3P5c

