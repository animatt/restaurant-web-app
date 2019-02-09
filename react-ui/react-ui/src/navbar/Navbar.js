import React, { Component } from 'react';
import {Link} from 'react-router-dom';

class Navbar extends Component {
	constructor(props) {
		super(props)
	}
	render() {
		const {loggedIn, userName} = this.props;
		let loginButton = <Link to="/login">Log in</Link>;
		if (loggedIn) {
			loginButton = <Link to="/logout">Log out</Link>;
		}
		return (
			<div className="col-sm-2">
			  <nav className="Navbar">
				{userName ? <h2>Welcome {userName}</h2> : null}
				<ul class="sidebar-nav">
				  <li><Link to="/">Home</Link></li>
				  <li>Restaurants</li>
				  <li>Reservations</li>
				  <li>{loginButton}</li>
				</ul>
			  </nav>
			</div>
		);
	}
}

export default Navbar;
