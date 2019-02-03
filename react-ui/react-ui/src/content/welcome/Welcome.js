import React, {Component} from 'react';
/* import { BrowserRouter as Router, Route, Link } from "react-router-dom"; */
import {BrowserRouter as Router, Route, Link} from 'react-router-dom';

class Welcome extends Component {
	constructor(props) {
		super(props);
	}
	render() {
		return (
			<div>
			  <header className="App-header">
				<h1>Welcome</h1>
			  </header>
			  <Link to="/reservation">Click here to make a reservation</Link>
			</div>
		);
	}
}

export default Welcome;
