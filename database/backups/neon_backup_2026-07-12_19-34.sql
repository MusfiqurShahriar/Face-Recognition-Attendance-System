--
-- PostgreSQL database dump
--

\restrict WeSWbSXviKJOLnVoxYnk7hyTXCxxRPPMXkjLfEVjfesRu8kQRXffpMnTeSgWQlW

-- Dumped from database version 17.10 (986efc8)
-- Dumped by pg_dump version 18.4

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: attendance; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.attendance (
    id integer NOT NULL,
    user_id character varying NOT NULL,
    name character varying NOT NULL,
    role character varying NOT NULL,
    roll_number character varying,
    section character varying,
    date character varying NOT NULL,
    "time" character varying NOT NULL,
    status character varying NOT NULL,
    semester character varying,
    created_at timestamp without time zone,
    course_id integer,
    session_id integer
);


ALTER TABLE public.attendance OWNER TO neondb_owner;

--
-- Name: attendance_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.attendance_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.attendance_id_seq OWNER TO neondb_owner;

--
-- Name: attendance_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.attendance_id_seq OWNED BY public.attendance.id;


--
-- Name: camera; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.camera (
    id integer NOT NULL,
    camera_code character varying(20) NOT NULL,
    room_name character varying(50),
    created_at timestamp without time zone,
    current_course_id integer,
    current_session_id integer
);


ALTER TABLE public.camera OWNER TO neondb_owner;

--
-- Name: camera_command; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.camera_command (
    id integer NOT NULL,
    camera_id integer NOT NULL,
    course_id integer NOT NULL,
    session_id integer NOT NULL,
    status character varying(20),
    created_at timestamp without time zone
);


ALTER TABLE public.camera_command OWNER TO neondb_owner;

--
-- Name: camera_command_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.camera_command_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.camera_command_id_seq OWNER TO neondb_owner;

--
-- Name: camera_command_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.camera_command_id_seq OWNED BY public.camera_command.id;


--
-- Name: camera_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.camera_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.camera_id_seq OWNER TO neondb_owner;

--
-- Name: camera_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.camera_id_seq OWNED BY public.camera.id;


--
-- Name: class_sessions; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.class_sessions (
    id integer NOT NULL,
    date character varying NOT NULL,
    section character varying NOT NULL,
    first_entry_time character varying,
    created_at timestamp without time zone,
    course_id integer,
    session_id integer
);


ALTER TABLE public.class_sessions OWNER TO neondb_owner;

--
-- Name: class_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.class_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.class_sessions_id_seq OWNER TO neondb_owner;

--
-- Name: class_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.class_sessions_id_seq OWNED BY public.class_sessions.id;


--
-- Name: course; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.course (
    id integer NOT NULL,
    session_id integer NOT NULL,
    course_code character varying(20) NOT NULL,
    course_name character varying(100) NOT NULL,
    section character varying(20),
    created_at timestamp without time zone
);


ALTER TABLE public.course OWNER TO neondb_owner;

--
-- Name: course_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.course_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.course_id_seq OWNER TO neondb_owner;

--
-- Name: course_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.course_id_seq OWNED BY public.course.id;


--
-- Name: cr_account; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.cr_account (
    id integer NOT NULL,
    session_id integer NOT NULL,
    name character varying(100) NOT NULL,
    login_email character varying(100) NOT NULL,
    login_password character varying(100) NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.cr_account OWNER TO neondb_owner;

--
-- Name: cr_account_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.cr_account_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.cr_account_id_seq OWNER TO neondb_owner;

--
-- Name: cr_account_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.cr_account_id_seq OWNED BY public.cr_account.id;


--
-- Name: enrollment; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.enrollment (
    id integer NOT NULL,
    course_id integer NOT NULL,
    user_id character varying(50) NOT NULL,
    name character varying(100),
    roll_number character varying(50),
    created_at timestamp without time zone
);


ALTER TABLE public.enrollment OWNER TO neondb_owner;

--
-- Name: enrollment_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.enrollment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.enrollment_id_seq OWNER TO neondb_owner;

--
-- Name: enrollment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.enrollment_id_seq OWNED BY public.enrollment.id;


--
-- Name: session; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.session (
    id integer NOT NULL,
    name character varying(20) NOT NULL,
    is_active integer,
    created_at timestamp without time zone
);


ALTER TABLE public.session OWNER TO neondb_owner;

--
-- Name: session_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.session_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.session_id_seq OWNER TO neondb_owner;

--
-- Name: session_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.session_id_seq OWNED BY public.session.id;


--
-- Name: attendance id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.attendance ALTER COLUMN id SET DEFAULT nextval('public.attendance_id_seq'::regclass);


--
-- Name: camera id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.camera ALTER COLUMN id SET DEFAULT nextval('public.camera_id_seq'::regclass);


--
-- Name: camera_command id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.camera_command ALTER COLUMN id SET DEFAULT nextval('public.camera_command_id_seq'::regclass);


--
-- Name: class_sessions id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.class_sessions ALTER COLUMN id SET DEFAULT nextval('public.class_sessions_id_seq'::regclass);


--
-- Name: course id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.course ALTER COLUMN id SET DEFAULT nextval('public.course_id_seq'::regclass);


--
-- Name: cr_account id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.cr_account ALTER COLUMN id SET DEFAULT nextval('public.cr_account_id_seq'::regclass);


--
-- Name: enrollment id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.enrollment ALTER COLUMN id SET DEFAULT nextval('public.enrollment_id_seq'::regclass);


--
-- Name: session id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.session ALTER COLUMN id SET DEFAULT nextval('public.session_id_seq'::regclass);


--
-- Data for Name: attendance; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.attendance (id, user_id, name, role, roll_number, section, date, "time", status, semester, created_at, course_id, session_id) FROM stdin;
\.


--
-- Data for Name: camera; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.camera (id, camera_code, room_name, created_at, current_course_id, current_session_id) FROM stdin;
\.


--
-- Data for Name: camera_command; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.camera_command (id, camera_id, course_id, session_id, status, created_at) FROM stdin;
\.


--
-- Data for Name: class_sessions; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.class_sessions (id, date, section, first_entry_time, created_at, course_id, session_id) FROM stdin;
\.


--
-- Data for Name: course; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.course (id, session_id, course_code, course_name, section, created_at) FROM stdin;
\.


--
-- Data for Name: cr_account; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.cr_account (id, session_id, name, login_email, login_password, created_at) FROM stdin;
\.


--
-- Data for Name: enrollment; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.enrollment (id, course_id, user_id, name, roll_number, created_at) FROM stdin;
\.


--
-- Data for Name: session; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.session (id, name, is_active, created_at) FROM stdin;
\.


--
-- Name: attendance_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.attendance_id_seq', 760, true);


--
-- Name: camera_command_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.camera_command_id_seq', 33, true);


--
-- Name: camera_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.camera_id_seq', 4, true);


--
-- Name: class_sessions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.class_sessions_id_seq', 21, true);


--
-- Name: course_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.course_id_seq', 45, true);


--
-- Name: cr_account_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.cr_account_id_seq', 5, true);


--
-- Name: enrollment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.enrollment_id_seq', 208, true);


--
-- Name: session_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.session_id_seq', 5, true);


--
-- Name: attendance attendance_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.attendance
    ADD CONSTRAINT attendance_pkey PRIMARY KEY (id);


--
-- Name: camera camera_camera_code_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.camera
    ADD CONSTRAINT camera_camera_code_key UNIQUE (camera_code);


--
-- Name: camera_command camera_command_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.camera_command
    ADD CONSTRAINT camera_command_pkey PRIMARY KEY (id);


--
-- Name: camera camera_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.camera
    ADD CONSTRAINT camera_pkey PRIMARY KEY (id);


--
-- Name: class_sessions class_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.class_sessions
    ADD CONSTRAINT class_sessions_pkey PRIMARY KEY (id);


--
-- Name: course course_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.course
    ADD CONSTRAINT course_pkey PRIMARY KEY (id);


--
-- Name: cr_account cr_account_login_email_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.cr_account
    ADD CONSTRAINT cr_account_login_email_key UNIQUE (login_email);


--
-- Name: cr_account cr_account_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.cr_account
    ADD CONSTRAINT cr_account_pkey PRIMARY KEY (id);


--
-- Name: enrollment enrollment_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.enrollment
    ADD CONSTRAINT enrollment_pkey PRIMARY KEY (id);


--
-- Name: session session_name_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.session
    ADD CONSTRAINT session_name_key UNIQUE (name);


--
-- Name: session session_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.session
    ADD CONSTRAINT session_pkey PRIMARY KEY (id);


--
-- Name: ix_attendance_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_attendance_id ON public.attendance USING btree (id);


--
-- Name: ix_class_sessions_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_class_sessions_id ON public.class_sessions USING btree (id);


--
-- Name: camera_command camera_command_camera_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.camera_command
    ADD CONSTRAINT camera_command_camera_id_fkey FOREIGN KEY (camera_id) REFERENCES public.camera(id);


--
-- Name: camera_command camera_command_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.camera_command
    ADD CONSTRAINT camera_command_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.course(id);


--
-- Name: camera_command camera_command_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.camera_command
    ADD CONSTRAINT camera_command_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.session(id);


--
-- Name: camera camera_current_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.camera
    ADD CONSTRAINT camera_current_course_id_fkey FOREIGN KEY (current_course_id) REFERENCES public.course(id);


--
-- Name: camera camera_current_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.camera
    ADD CONSTRAINT camera_current_session_id_fkey FOREIGN KEY (current_session_id) REFERENCES public.session(id);


--
-- Name: course course_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.course
    ADD CONSTRAINT course_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.session(id);


--
-- Name: cr_account cr_account_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.cr_account
    ADD CONSTRAINT cr_account_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.session(id);


--
-- Name: enrollment enrollment_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.enrollment
    ADD CONSTRAINT enrollment_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.course(id);


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: public; Owner: cloud_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE cloud_admin IN SCHEMA public GRANT ALL ON SEQUENCES TO neon_superuser WITH GRANT OPTION;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: cloud_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE cloud_admin IN SCHEMA public GRANT ALL ON TABLES TO neon_superuser WITH GRANT OPTION;


--
-- PostgreSQL database dump complete
--

\unrestrict WeSWbSXviKJOLnVoxYnk7hyTXCxxRPPMXkjLfEVjfesRu8kQRXffpMnTeSgWQlW

